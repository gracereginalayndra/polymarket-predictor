"""Chronological holdout with whole-event purging and label-maturity embargo."""
import pandas as pd

from src.dataset.leakage_checks import check_disjoint_groups, check_training_labels


def chronological_split(frame, train_end, validation_end):
    if train_end >= validation_end:
        raise ValueError('train_end must precede validation_end')
    data = frame.copy()
    if data.empty:
        raise ValueError('Empty dataset')
    if len(set(data.source_kind)) != 1:
        raise ValueError('Mixed source kinds')
    group = data.groupby('event_group').agg(first=('cutoff', 'min'), last=('cutoff', 'max'))
    train_groups = group.index[group['last'] < train_end]
    validation_groups = group.index[(group['first'] >= train_end) & (group['last'] < validation_end)]
    test_groups = group.index[group['first'] >= validation_end]
    # Entire groups with any unmatured/missing label are removed from fitting/tuning.
    def mature(ids, deadline):
        part = data[data.event_group.isin(ids)]
        good = part.groupby('event_group').apply(
            lambda x: bool(x.outcome.notna().all() and x.label_available_at.notna().all()
                           and (x.label_available_at <= deadline).all()), include_groups=False)
        return set(good.index[good]) if len(good) else set()
    train_groups = mature(train_groups, train_end)
    validation_groups = mature(validation_groups, validation_end)
    train = data[data.event_group.isin(train_groups)].copy()
    validation = data[data.event_group.isin(validation_groups)].copy()
    test = data[data.event_group.isin(test_groups)].copy()
    check_disjoint_groups(train, validation, test)
    if not train.empty:
        check_training_labels(train, train_end)
    if not validation.empty:
        check_training_labels(validation, validation_end)
    used = set(train.event_group) | set(validation.event_group) | set(test.event_group)
    purged = data[~data.event_group.isin(used)].copy()
    return train, validation, test, purged


def group_weights(frame):
    """Equal weight per event, per market within event, per snapshot within market."""
    markets_per_event = frame.groupby('event_group').market_id.transform('nunique')
    snapshots_per_market = frame.groupby(['event_group', 'market_id']).snapshot_id.transform('count')
    return (1 / (markets_per_event * snapshots_per_market)).to_numpy()
