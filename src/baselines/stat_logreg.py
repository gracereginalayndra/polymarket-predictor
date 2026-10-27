import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MARKET_FEATURES = ['logit_market', 'price_change_24h', 'missing_history', 'spread',
                   'missing_spread', 'log_volume', 'log_liquidity', 'horizon_hours']


def design(frame, columns):
    values = frame.copy()
    values['logit_market'] = logit(values['market_price'])
    for col in columns:
        if col.startswith('logit_') and col != 'logit_market':
            values[col] = logit(values[col[len('logit_'):]])
    result = values[columns].to_numpy(dtype=float)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite model features; do not silently impute failed agents')
    return result


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1-1e-6)
    return np.log(p)-np.log1p(-p)


class LogisticModel:
    def __init__(self, columns, regularization=1.0):
        self.columns = columns
        self.pipeline = Pipeline([('scale', StandardScaler()),
                                  ('logistic', LogisticRegression(C=regularization, max_iter=2000, random_state=2605))])

    def fit(self, frame, weights):
        if frame.outcome.nunique() < 2:
            raise ValueError('Need both YES and NO in training')
        self.pipeline.fit(design(frame, self.columns), frame.outcome.astype(int),
                          scale__sample_weight=weights, logistic__sample_weight=weights)
        return self

    def predict(self, frame):
        return self.pipeline.predict_proba(design(frame, self.columns))[:, 1]

    def describe(self):
        return {'columns': self.columns, 'coefficients_scaled': self.pipeline['logistic'].coef_[0].tolist(),
                'intercept': float(self.pipeline['logistic'].intercept_[0]),
                'feature_mean': self.pipeline['scale'].mean_.tolist(),
                'feature_scale': self.pipeline['scale'].scale_.tolist()}
