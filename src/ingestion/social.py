"""Bounded public Reddit adapter and licensed/exported social JSONL import."""
import re

from src.common import read_jsonl, timestamp
from src.db.loaders import add_document


def collect_reddit(client, con, subreddit):
    if not re.fullmatch(r'[A-Za-z0-9_]{2,30}', subreddit):
        raise ValueError('Invalid subreddit name')
    payload, observed, ref = client.get(f'https://www.reddit.com/r/{subreddit}/new.json', {'limit': 100})
    count = 0
    for item in payload['data']['children']:
        post = item['data']
        published = timestamp(post['created_utc'])
        if published > observed:
            continue
        count += int(add_document(con, dict(url='https://www.reddit.com'+post['permalink'],
            title=post['title'], body=post.get('selftext', ''), source='reddit.com', source_type='social',
            published_at=published, available_at=observed, observed_at=observed,
            provenance='prospective', raw_ref=ref, source_kind='real', content_kind='post')))
    return count


def import_documents(con, path, source_type=None):
    count = 0
    for row in read_jsonl(path):
        if source_type and row['source_type'] != source_type:
            raise ValueError('Wrong source_type in import')
        for key in ('published_at', 'available_at', 'observed_at'):
            row[key] = timestamp(row[key])
        if row.get('source_kind') != 'real':
            raise ValueError('Research imports must be real; use run_demo for synthetic data')
        count += int(add_document(con, row))
    return count
