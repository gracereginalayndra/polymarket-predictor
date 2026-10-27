import unittest
import pandas as pd

from src.dataset.leakage_checks import check_evidence, check_snapshot, check_training_labels
from src.dataset.splits import chronological_split, group_weights


class LeakageTests(unittest.TestCase):
    def test_old_publication_new_observation(self):
        d = dict(source_kind='real', published_at=1, available_at=11, observed_at=11, provenance='prospective')
        with self.assertRaises(ValueError):
            check_evidence([d],10,'real')

    def test_faked_available_timestamp(self):
        d = dict(source_kind='real', published_at=1, available_at=2, observed_at=11, provenance='prospective')
        with self.assertRaises(ValueError):
            check_evidence([d],10,'real')

    def test_archive_can_be_ingested_later(self):
        d = dict(source_kind='real', published_at=1, available_at=2, observed_at=11, provenance='archive_verified')
        check_evidence([d],10,'real')

    def test_settlement_rejected(self):
        m = dict(available_at=1,scheduled_end=20,provenance='synthetic')
        p = dict(timestamp=9,available_at=9,resolution_seconds=0,provenance='synthetic')
        with self.assertRaises(ValueError):
            check_snapshot({'cutoff':10},m,p)

    def test_future_training_labels(self):
        df = pd.DataFrame({'outcome':[1],'label_available_at':[11],'cutoff':[1]})
        with self.assertRaises(ValueError):
            check_training_labels(df,10)

    def test_groups_straddling_split_purged(self):
        df = pd.DataFrame({'event_group':['a','b','b','c','d'], 'market_id':['a','b1','b2','c','d'],
            'snapshot_id':list('abcde'),'cutoff':[1,4,6,7,11], 'outcome':[0,1,1,0,1],
            'label_available_at':[2,8,8,9,12],'source_kind':['synthetic']*5})
        train,val,test,purged = chronological_split(df,5,10)
        self.assertEqual(set(train.event_group),{'a'})
        self.assertEqual(set(val.event_group),{'c'})
        self.assertEqual(set(test.event_group),{'d'})
        self.assertEqual(set(purged.event_group),{'b'})

    def test_unmatured_group_purged(self):
        df = pd.DataFrame({'event_group':['a','b','c'], 'market_id':['a','b','c'],
            'snapshot_id':list('abc'),'cutoff':[1,7,11], 'outcome':[0,1,1],
            'label_available_at':[8,9,12],'source_kind':['synthetic']*3})
        train,_,_,purged = chronological_split(df,5,10)
        self.assertTrue(train.empty)
        self.assertIn('a',set(purged.event_group))

    def test_equal_event_weights(self):
        df=pd.DataFrame({'event_group':['a','a','a','b'],'market_id':['x','x','y','z'],'snapshot_id':list('abcd')})
        self.assertEqual(group_weights(df).tolist(),[.25,.25,.5,1.])
