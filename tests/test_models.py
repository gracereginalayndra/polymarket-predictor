import unittest
import numpy as np
import pandas as pd

from src.models.calibrator import BayesianLogisticCorrection
from src.baselines.stat_logreg import LogisticModel


class ModelTests(unittest.TestCase):
    def test_bayesian_finite_and_intervals(self):
        df=pd.DataFrame({'market_price':[.2,.4,.7,.9]*5,'multi_verified':[.1,.6,.8,.95]*5,
                         'outcome':[0,0,1,1]*5})
        model=BayesianLogisticCorrection().fit(df,np.ones(len(df)))
        p=model.predict(df);bounds=model.intervals(df)
        self.assertTrue(np.all((p>0)&(p<1)))
        self.assertTrue(np.all(bounds[:,0]<=p))
        self.assertTrue(np.all(bounds[:,1]>=p))

    def test_logistic_one_class_refused(self):
        df=pd.DataFrame({'market_price':[.2,.3],'outcome':[1,1]})
        with self.assertRaises(ValueError):
            LogisticModel(['logit_market']).fit(df,np.ones(2))
