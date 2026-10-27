import argparse
import json

from src.common import load_config
from src.db.loaders import connect
from src.models.training import fit


def main():
    parser = argparse.ArgumentParser(description='Tune on validation, refit on mature train+validation, leave test untouched.')
    parser.add_argument('--config', default='configs/config.yaml')
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    con = connect(cfg['database'])
    path, manifest = fit(con, cfg, args.run_id)
    print(json.dumps({'artifact_directory': str(path), 'status': manifest['status'],
                      'train_groups': manifest['train_groups'], 'validation_groups': manifest['validation_groups']}, indent=2))
    con.close()


if __name__ == '__main__':
    main()
