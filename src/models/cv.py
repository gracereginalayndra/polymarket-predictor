"""Expanding temporal folds with group purging and known-label checks."""
import numpy as np

from src.dataset.splits import chronological_split


def purged_walk_forward(frame, folds=3):
    times = np.sort(frame.cutoff.unique())
    if len(times) < folds+3:
        raise ValueError('Too few time points for walk-forward CV')
    boundaries = np.unique(np.quantile(times, np.linspace(.4, 1, folds+1)).astype(int))
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        train, validation, _, _ = chronological_split(frame, int(left), int(right)+1)
        if not train.empty and not validation.empty and train.outcome.nunique() == 2:
            yield train, validation
