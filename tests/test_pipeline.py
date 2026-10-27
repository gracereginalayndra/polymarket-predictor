import tempfile
import unittest

from scripts.run_demo import demo_config, populate
from src.db.loaders import connect
from src.dataset.snapshots import build, frame
from src.agents.orchestrator import run_agents
from src.models.training import fit
from src.evaluation.report import evaluate


class PipelineTests(unittest.TestCase):
    def test_full_pipeline_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=demo_config(d)
            cfg['training'].update(train_end='2025-02-14T00:00:00Z',validation_end='2025-03-15T00:00:00Z',
                                   min_train_groups=8,min_validation_groups=5)
            cfg['evaluation']['bootstrap_samples']=30
            con=connect(cfg['database'])
            try:
                populate(con,cfg,groups=40)
                build(con,cfg)
                result=run_agents(con,frame(con),cfg)
                self.assertEqual(result['failures'],[])
                resumed=run_agents(con,frame(con),cfg)
                self.assertEqual(resumed['calls'],0)
                path,manifest=fit(con,cfg,result['run_id'])
                self.assertEqual(len(manifest['parameters']),7)
                report=evaluate(con,cfg,result['run_id'])
                self.assertEqual(report['status'],'SYNTHETIC_DEMONSTRATION_ONLY')
                self.assertGreater(report['event_groups'],0)
                self.assertTrue((path/'calibration.png').exists())
            finally:
                con.close()
