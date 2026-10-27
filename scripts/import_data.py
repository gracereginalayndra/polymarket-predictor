import argparse

from src.common import load_config, read_jsonl, timestamp
from src.db.loaders import connect, insert
from src.ingestion.social import import_documents
from src.ingestion.external import import_releases


def main():
    parser = argparse.ArgumentParser(description='Import licensed evidence or reviewed archival records. See docs/data_spec.md.')
    parser.add_argument('--config', default='configs/config.yaml')
    parser.add_argument('--kind', choices=['documents','releases','markets','market_versions','prices','resolutions'], required=True)
    parser.add_argument('--file', required=True)
    parser.add_argument('--archive-verified', action='store_true', help='Attest archival source/version timestamps were manually reviewed')
    args = parser.parse_args()
    cfg = load_config(args.config)
    con = connect(cfg['database'])
    if args.kind == 'documents':
        count = import_documents(con, args.file)
    elif args.kind == 'releases':
        count = import_releases(con, args.file)
    else:
        count = 0
        for row in read_jsonl(args.file):
            if args.kind in ('market_versions','prices','resolutions') and not args.archive_verified:
                raise ValueError('Archival import requires --archive-verified and documented source review')
            for key in ('timestamp','available_at','observed_at','scheduled_end','resolved_at','label_available_at'):
                if key in row:
                    row[key] = timestamp(row[key])
            if args.kind in ('market_versions','prices'):
                if row['provenance'] != 'archive_verified' or not row['raw_ref']:
                    raise ValueError('Require verified archival provenance and source reference')
            if args.kind == 'markets' and row['source_kind'] != 'real':
                raise ValueError('Synthetic imports are prohibited in research data')
            if args.kind == 'resolutions' and (not row['raw_ref'] or row['label_available_at'] < row['resolved_at']):
                raise ValueError('Invalid resolution provenance/timing')
            count += int(insert(con, args.kind, row))
    con.close()
    print(f'Imported {count} records')


if __name__ == '__main__':
    main()
