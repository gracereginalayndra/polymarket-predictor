import argparse
import json
from pathlib import Path

from src.common import load_config, write_json
from src.db.loaders import connect
from src.dataset.snapshots import frame
from src.agents.orchestrator import run_agents


def main():
    parser = argparse.ArgumentParser(description='Generate auditable forecasts; real calls require configured credentials.')
    parser.add_argument('--config', default='configs/config.yaml')
    parser.add_argument('--limit', type=int, help='Pilot limit; selection is chronological, never based on outcomes')
    args = parser.parse_args()
    cfg = load_config(args.config)
    con = connect(cfg['database'])
    data = frame(con)
    if args.limit:
        data = data.head(args.limit)
    result = run_agents(con, data, cfg)
    write_json(Path(cfg['artifact_dir'])/'agents_latest.json', result)
    print(json.dumps(result, indent=2))
    con.close()
    return 2 if result['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
