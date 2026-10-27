"""Timestamped economic/financial release import, retaining release-vintage provenance."""
import csv

from src.common import timestamp, utcnow
from src.db.loaders import add_document


def import_releases(con, path):
    count, observed = 0, utcnow()
    with open(path, encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            published = timestamp(row['released_at'])
            if published > observed:
                raise ValueError('Release timestamp is in the future')
            count += int(add_document(con, dict(url=row['source_url'], title=row['series'],
                body=f"Reference period: {row['period']}; released value: {row['value']}; units: {row['units']}",
                source=row['source'], source_type='external', published_at=published,
                available_at=observed, observed_at=observed, provenance='prospective',
                raw_ref=str(path), source_kind='real', content_kind='release_vintage')))
    return count
