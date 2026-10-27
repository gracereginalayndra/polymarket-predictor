"""A full, deterministic SYNTHETIC integration run. Never a substitute for FYP results."""
import argparse
from copy import deepcopy
from pathlib import Path

import numpy as np
import yaml
from scipy.special import expit

from src.common import ROOT, digest, load_config, timestamp, write_json
from src.db.loaders import connect, insert, add_document
from src.dataset.snapshots import build, frame
from src.agents.orchestrator import run_agents
from src.models.training import fit
from src.evaluation.report import evaluate


def demo_config(output):
    cfg = deepcopy(load_config())
    output = Path(output).resolve()
    cfg.update(mode='synthetic', database=str(output/'demo.sqlite'), data_dir=str(output/'data'),
               artifact_dir=str(output/'artifacts'), config_path=str(output/'demo_config.yaml'))
    cfg['llm'].update(provider='mock', model='synthetic-test-backend', max_calls_per_run=10000)
    cfg['dataset'].update(horizons_hours=[24,168], max_price_age_seconds=7200)
    cfg['training'].update(train_end='2025-07-05T00:00:00Z', validation_end='2025-10-03T00:00:00Z',
                           min_train_groups=30, min_validation_groups=10)
    cfg['evaluation']['bootstrap_samples'] = 500
    output.mkdir(parents=True, exist_ok=True)
    (output/'demo_config.yaml').write_text(yaml.safe_dump(cfg))
    return cfg


def populate(con, cfg, groups=140):
    rng = np.random.default_rng(cfg['seed'])
    start = timestamp('2025-01-01T00:00:00Z')
    for g in range(groups):
        deadline = start+(g*3+10)*86400
        tag = f'event{g:04d}'
        latent = rng.normal()
        true_p = float(expit(latent))
        outcome = int(rng.random() < true_p)
        news_signal = float(expit(latent+rng.normal(0, .75)))
        social_signal = float(expit(latent+rng.normal(0, 1.5)))
        for source, signal, source_type in [('news.test',news_signal,'news'),('social.test',social_signal,'social')]:
            published = deadline-9*86400
            add_document(con, dict(url=f'https://{source}/{tag}', title=f'{tag} {tag} policy research bulletin',
                body=f'{tag} {tag} {tag} policy outlook. SYNTHETIC_SIGNAL={signal:.6f}. This is artificial test evidence.',
                source=source, source_type=source_type, published_at=published,
                available_at=published+60, observed_at=published+60, provenance='synthetic',
                raw_ref='generated_by_run_demo', source_kind='synthetic', content_kind='synthetic_signal'))
        for member in range(2):
            mid = f'SYNTHETIC_{g:04d}_{member}'
            insert(con, 'markets', dict(market_id=mid, condition_id=mid, event_group=tag,
                yes_token=mid+'_yes', no_token=mid+'_no', yes_index=0, source_kind='synthetic'))
            metadata = dict(market_id=mid, available_at=deadline-10*86400, observed_at=deadline-10*86400,
                question=f'Will the synthetic {tag} policy outcome be YES for contract {member}?',
                rules=f'Synthetic {tag} policy test. YES if the simulated binary event occurs by the scheduled deadline.',
                scheduled_end=deadline, category='synthetic', is_open=1, liquidity=10000., volume=50000.,
                provenance='synthetic', raw_ref='generated_by_run_demo')
            metadata['version_id'] = digest(metadata)
            insert(con, 'market_versions', metadata)
            for horizon in cfg['dataset']['horizons_hours']:
                cutoff = deadline-int(horizon*3600)
                p = float(np.clip(expit(latent+rng.normal(0, .85)), .03, .97))
                for ago, value in [(60, p), (86460, float(np.clip(p+rng.normal(0,.03), .03,.97)))]:
                    record = dict(market_id=mid, timestamp=cutoff-ago, available_at=cutoff-ago,
                        observed_at=cutoff-ago, price=value, price_kind='midpoint', resolution_seconds=1,
                        bid=max(value-.01,0), ask=min(value+.01,1), provenance='synthetic', raw_ref='generated_by_run_demo')
                    record['price_id'] = digest(record)
                    insert(con, 'prices', record)
            resolved = deadline+(6*86400 if g % 9 == 0 else 7200)
            insert(con, 'resolutions', dict(market_id=mid, outcome=outcome, resolved_at=resolved,
                label_available_at=resolved+60, observed_at=resolved+60, source='synthetic_generator',
                status='final', raw_ref='generated_by_run_demo'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT/'artifacts'/'demo'))
    args = parser.parse_args()
    cfg = demo_config(args.output)
    con = connect(cfg['database'])
    populate(con, cfg)
    snapshots = build(con, cfg)
    print(f'SYNTHETIC ONLY: {snapshots["eligible"]} eligible snapshots', flush=True)
    generated = run_agents(con, frame(con), cfg)
    if generated['failures']:
        write_json(Path(args.output)/'failures.json', generated)
        raise RuntimeError('Synthetic integration failed; inspect failures.json')
    path, manifest = fit(con, cfg, generated['run_id'])
    report = evaluate(con, cfg, generated['run_id'])
    summary = {'status': 'SYNTHETIC_DEMONSTRATION_ONLY', 'snapshots': snapshots['eligible'],
        'train_groups': manifest['train_groups'], 'validation_groups': manifest['validation_groups'],
        'test_groups': report['event_groups'], 'models_fitted': len(manifest['parameters']),
        'forecast_run': generated, 'artifact_directory': str(path),
        'warning': 'This validates software execution only. It does NOT show forecasting accuracy on real markets.'}
    write_json(Path(args.output)/'demo_summary.json', summary)
    print(summary, flush=True)
    con.close()


if __name__ == '__main__':
    main()
