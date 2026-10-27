import argparse
import json

from src.common import load_config
from src.db.loaders import connect
from src.evaluation.report import evaluate


def main():
    parser = argparse.ArgumentParser(description='Evaluate held-out data with paired event-cluster uncertainty.')
    parser.add_argument('--config', default='configs/config.yaml')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--allow-exploratory', action='store_true', help='Explicitly label unfrozen real analyses exploratory')
    args = parser.parse_args()
    cfg = load_config(args.config)
    con = connect(cfg['database'])
    report = evaluate(con, cfg, args.run_id, args.allow_exploratory)
    print(json.dumps({k: report[k] for k in ['status','event_groups','common_rows','scores_on_common_cohort']}, indent=2))
    con.close()


if __name__ == '__main__':
    main()
