"""Run public collectors; failures are persisted and cause exit status 2."""
import argparse
import json
from pathlib import Path

from src.common import load_config, utcnow, write_json
from src.db.loaders import connect, rows, event
from src.ingestion.http import HTTPClient
from src.ingestion import gamma, clob, data_api, news, social


def run(cfg, stages):
    con, client = connect(cfg['database']), HTTPClient(cfg)
    report = {'started_at': utcnow(), 'successes': [], 'failures': []}
    def attempt(stage, identity, action):
        try:
            output = action()
            report['successes'].append({'stage': stage, 'identity': identity,
                                        'result': output if isinstance(output, int) else 1})
        except Exception as exc:
            failure = {'stage': stage, 'identity': identity, 'error': type(exc).__name__+': '+str(exc)}
            report['failures'].append(failure)
            event(con, stage, 'failed', failure)
    if 'markets' in stages:
        attempt('markets', 'gamma', lambda: gamma.collect(client, con, cfg))
    markets = rows(con, '''SELECT m.* FROM markets m JOIN market_versions v USING(market_id)
                   WHERE source_kind=? GROUP BY m.market_id ORDER BY MAX(v.observed_at) DESC,m.market_id LIMIT ?''',
                   ('real', cfg['polymarket']['max_markets']))
    for market in markets:
        if 'quotes' in stages:
            attempt('quotes', market['market_id'], lambda: clob.collect_quote(client, con, cfg, market))
        if 'history' in stages:
            backend = cfg['polymarket']['history_backend']
            if backend not in ('v2', 'legacy_clob'):
                raise ValueError('history_backend must be v2 or legacy_clob')
            collector = data_api.collect_history if backend == 'v2' else clob.legacy_history
            end = utcnow()
            attempt('history', market['market_id'], lambda: collector(client, con, cfg, market,
                end-int(cfg['polymarket']['history_days']*86400), end))
        if 'resolutions' in stages:
            attempt('resolutions', market['market_id'], lambda: data_api.collect_resolution(client, con, cfg, market))
    if 'news' in stages:
        for url in cfg['news']['rss_urls']:
            attempt('rss', url, lambda: news.collect_rss(client, con, url))
        for query in cfg['news']['gdelt_queries']:
            attempt('gdelt', query, lambda: news.collect_gdelt(client, con, query))
    if 'social' in stages:
        for subreddit in cfg['social']['subreddits']:
            attempt('reddit', subreddit, lambda: social.collect_reddit(client, con, subreddit))
    report['finished_at'] = utcnow()
    write_json(Path(cfg['artifact_dir'])/'ingestion_latest.json', report)
    event(con, 'ingest', 'partial' if report['failures'] else 'complete', report)
    con.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/config.yaml')
    parser.add_argument('--stages', default='markets,quotes,news', help='Comma-separated markets,quotes,history,news,social,resolutions')
    args = parser.parse_args()
    stages = set(args.stages.split(','))
    if not stages <= {'markets','quotes','history','news','social','resolutions'}:
        parser.error('Unknown stage')
    result = run(load_config(args.config), stages)
    print(json.dumps(result, indent=2))
    return 2 if result['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
