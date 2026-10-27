import numpy as np

from src.evaluation.metrics import validate


def reliability(y, p, weights=None, bins=5):
    y, p, w = validate(y, p, weights)
    groups = np.minimum((p*bins).astype(int), bins-1)
    results = []
    for i in range(bins):
        use = groups == i
        if use.any():
            results.append({'bin': i, 'left': i/bins, 'right': (i+1)/bins,
                'count': int(use.sum()), 'weight': float(w[use].sum()),
                'mean_prediction': float(np.average(p[use], weights=w[use])),
                'observed_frequency': float(np.average(y[use], weights=w[use]))})
    return results


def plot_calibration(curves, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([0, 1], [0, 1], '--', color='gray', label='Perfect calibration')
    for name, curve in curves.items():
        ax.plot([b['mean_prediction'] for b in curve], [b['observed_frequency'] for b in curve],
                'o-', label=name, markersize=4)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='Mean forecast probability', ylabel='Observed YES frequency', title=title)
    ax.legend(fontsize=8, loc='best')
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
