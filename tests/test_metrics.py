import unittest
import numpy as np
import pandas as pd

from src.evaluation.metrics import brier_score, log_loss
from src.evaluation.calibration import reliability
from src.evaluation.stats_tests import paired_cluster_bootstrap


class MetricsTests(unittest.TestCase):
    def test_known_brier(self):
        self.assertEqual(brier_score([0,1], [.5,.5]), .25)
        self.assertEqual(brier_score([0,1], [0,1]), 0)

    def test_log_loss_extremes(self):
        self.assertTrue(np.isfinite(log_loss([1,0], [0,1])))
        self.assertAlmostEqual(log_loss([0,1],[.5,.5]), np.log(2))

    def test_invalid_predictions(self):
        for p in ([float('nan')], [1.1], [-.1]):
            with self.assertRaises(ValueError):
                brier_score([1], p)

    def test_calibration_endpoints(self):
        r = reliability([0,1], [0,1], bins=5)
        self.assertEqual([a['bin'] for a in r], [0,4])

    def test_cluster_not_row_count(self):
        df = pd.DataFrame({'event_group':['a']*100+['b'], 'market_id':['x']*100+['z'],
                           'outcome':[1]*101, 'model':[1]*100+[0], 'reference':[.5]*101})
        out = paired_cluster_bootstrap(df, 'model','reference',samples=100)
        self.assertEqual(out['event_groups'],2)
        self.assertAlmostEqual(out['mean_brier_difference'], .25)

    def test_paired_identical(self):
        df = pd.DataFrame({'event_group':['a','b'],'market_id':['x','z'],
                           'outcome':[0,1],'a':[.2,.8],'b':[.2,.8]})
        out = paired_cluster_bootstrap(df,'a','b',samples=50)
        self.assertEqual(out['ci95'],[0.,0.])
