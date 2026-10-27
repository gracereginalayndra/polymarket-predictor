import numpy as np


def validate(y, p, weights=None):
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    if y.shape != p.shape or y.ndim != 1 or not len(y):
        raise ValueError('Nonempty aligned one-dimensional outcomes/probabilities required')
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Nonfinite outcome/probability')
    if not np.isin(y, [0, 1]).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid binary outcome/probability')
    w = np.ones_like(y) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != y.shape or not np.isfinite(w).all() or (w < 0).any() or w.sum() <= 0:
        raise ValueError('Invalid weights')
    return y, p, w


def brier_score(y, p, weights=None):
    y, p, w = validate(y, p, weights)
    return float(np.average((p-y)**2, weights=w))


def log_loss(y, p, weights=None, epsilon=1e-6):
    y, p, w = validate(y, p, weights)
    if not 0 < epsilon < .5:
        raise ValueError('Invalid clipping epsilon')
    p = np.clip(p, epsilon, 1-epsilon)
    return float(np.average(-y*np.log(p)-(1-y)*np.log1p(-p), weights=w))


def score(y, p, weights=None, epsilon=1e-6):
    return {'brier': brier_score(y, p, weights), 'log_loss': log_loss(y, p, weights, epsilon)}
