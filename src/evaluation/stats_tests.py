import numpy as np


def paired_cluster_bootstrap(frame, system, reference, samples=2000, seed=2605):
    """Paired differences, first averaged within market then within event group."""
    use = frame.dropna(subset=['outcome', system, reference]).copy()
    if use.empty:
        raise ValueError('No paired predictions')
    use['difference'] = (use[system]-use.outcome)**2-(use[reference]-use.outcome)**2
    market_means = use.groupby(['event_group', 'market_id']).difference.mean()
    group_means = market_means.groupby(level=0).mean().to_numpy()
    if len(group_means) < 2:
        return {'mean_brier_difference': float(group_means.mean()), 'ci95': None,
                'event_groups': len(group_means), 'warning': 'Too few groups for uncertainty estimate'}
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(group_means, len(group_means), replace=True).mean() for _ in range(samples)])
    return {'mean_brier_difference': float(group_means.mean()),
            'ci95': np.quantile(means, [.025, .975]).tolist(), 'event_groups': len(group_means),
            'interpretation': 'Negative favors system; event-cluster percentile bootstrap, not causal evidence.'}
