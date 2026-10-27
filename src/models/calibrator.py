"""Supervised stacking plus optional Normal-prior logistic correction to market odds."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from src.baselines.stat_logreg import LogisticModel, MARKET_FEATURES, logit

MODEL_COLUMNS = {
    'market_calibrated': ['logit_market'],
    'stat_logreg': MARKET_FEATURES,
    'hybrid_single': MARKET_FEATURES+['logit_single_agent_rag'],
    'hybrid_unverified': MARKET_FEATURES+['logit_multi_unverified'],
    'hybrid_verified': MARKET_FEATURES+['logit_multi_verified'],
    'hybrid_no_social': MARKET_FEATURES+['logit_multi_no_social'],
}


def logistic_model(name, regularization):
    return LogisticModel(MODEL_COLUMNS[name], regularization)


class BayesianLogisticCorrection:
    """MAP + Laplace approximation under an event-weighted working likelihood.

    This is a sensitivity model, not an exact hierarchical posterior. A fixed market
    log-odds offset and Normal(0, prior_sd) weights shrink back toward the market.
    """
    def __init__(self, prior_sd=1.0):
        if prior_sd <= 0:
            raise ValueError('prior_sd must be positive')
        self.prior_sd = prior_sd

    def matrix(self, frame):
        market = logit(frame.market_price)
        return np.column_stack([np.ones(len(frame)), logit(frame.multi_verified)-market]), market

    def fit(self, frame, weights):
        x, offset = self.matrix(frame)
        y, w = frame.outcome.to_numpy(dtype=float), np.asarray(weights)
        precision = 1/self.prior_sd**2
        def objective(beta):
            z = offset+x@beta
            return np.sum(w*(np.logaddexp(0, z)-y*z))+.5*precision*np.dot(beta, beta)
        def gradient(beta):
            return x.T@(w*(expit(offset+x@beta)-y))+precision*beta
        result = minimize(objective, np.zeros(x.shape[1]), jac=gradient, method='BFGS')
        if not result.success and np.linalg.norm(gradient(result.x)) > 1e-4:
            raise ValueError('Bayesian MAP optimizer did not converge')
        self.beta = result.x
        p = expit(offset+x@self.beta)
        hessian = x.T@((w*p*(1-p))[:, None]*x)+precision*np.eye(x.shape[1])
        self.covariance = np.linalg.inv(hessian)
        return self

    def predict(self, frame):
        x, offset = self.matrix(frame)
        return expit(offset+x@self.beta)

    def intervals(self, frame):
        x, offset = self.matrix(frame)
        mean = offset+x@self.beta
        sd = np.sqrt(np.einsum('ij,jk,ik->i', x, self.covariance, x))
        return np.column_stack([expit(mean-1.96*sd), expit(mean+1.96*sd)])

    def describe(self):
        return {'beta': self.beta.tolist(), 'covariance': self.covariance.tolist(), 'prior_sd': self.prior_sd,
                'warning': 'Working-likelihood Laplace intervals; not calibrated event-probability bounds.'}
