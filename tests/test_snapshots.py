import tempfile
import unittest

from scripts.run_demo import demo_config, populate
from src.db.loaders import connect, rows
from src.dataset.snapshots import build, frame
from src.retrieval.temporal_retriever import retrieve


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.cfg=demo_config(self.tmp.name)
        self.con=connect(self.cfg['database'])
        populate(self.con,self.cfg,groups=3)

    def tearDown(self):
        self.con.close();self.tmp.cleanup()

    def test_snapshot_count_and_idempotence(self):
        self.assertEqual(build(self.con,self.cfg)['eligible'],12)
        build(self.con,self.cfg)
        self.assertEqual(len(frame(self.con)),12)

    def test_retrieval_asof(self):
        build(self.con,self.cfg)
        row=frame(self.con).iloc[0].to_dict()
        docs=retrieve(self.con,row,self.cfg)
        self.assertGreater(len(docs),0)
        self.assertTrue(all(d['available_at'] <= row['cutoff'] for d in docs))
        self.assertTrue(all(d['source_type']!='social' for d in retrieve(self.con,row,self.cfg,False)))

    def test_stale_price_exclusion(self):
        self.cfg['dataset']['max_price_age_seconds']=10
        out=build(self.con,self.cfg)
        self.assertEqual(out['eligible'],0)
        self.assertTrue(all(e['reason']=='stale_price' for e in out['excluded']))
