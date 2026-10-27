"""RSS/Atom and GDELT discovery. Headline-only records are explicitly labelled."""
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from src.common import timestamp
from src.db.loaders import add_document


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(text):
    parser = TextParser()
    parser.feed(text or '')
    return unescape(' '.join(parser.parts)).strip()


def rss_records(xml, observed, ref):
    root = ET.fromstring(xml)
    for item in list(root.findall('.//item')) + list(root.findall('{http://www.w3.org/2005/Atom}entry')):
        fields = {node.tag.split('}')[-1]: node for node in item}
        def value(key):
            node = fields.get(key)
            return '' if node is None else (node.text or '')
        link_node = fields.get('link')
        url = value('link') or (link_node.get('href', '') if link_node is not None else '')
        when = value('pubDate') or value('published') or value('updated')
        if not url or not when:
            continue
        try:
            published = timestamp(when)
        except ValueError:
            dt = parsedate_to_datetime(when)
            if dt.tzinfo is None:
                continue
            published = int(dt.timestamp())
        if published > observed:
            continue
        body = plain(value('description') or value('summary') or value('content'))
        yield dict(url=url, title=plain(value('title')), body=body,
                   source=urlsplit(url).netloc, source_type='news', published_at=published,
                   available_at=observed, observed_at=observed, provenance='prospective',
                   raw_ref=ref, source_kind='real', content_kind='feed_summary' if body else 'headline')


def collect_rss(client, con, url):
    payload, observed, ref = client.get(url, json_response=False)
    return sum(int(add_document(con, r)) for r in rss_records(payload, observed, ref))


def collect_gdelt(client, con, query):
    payload, observed, ref = client.get('https://api.gdeltproject.org/api/v2/doc/doc',
        {'query': query, 'mode': 'artlist', 'format': 'json', 'maxrecords': 100, 'timespan': '1d'})
    n = 0
    for article in payload.get('articles', []):
        # GDELT seendate is discovery time, not guaranteed original publication time.
        from datetime import datetime, timezone
        seen = int(datetime.strptime(article['seendate'], '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc).timestamp())
        if seen > observed:
            continue
        n += int(add_document(con, dict(url=article['url'], title=article['title'], body='',
            source=article.get('domain') or urlsplit(article['url']).netloc, source_type='news',
            published_at=seen, available_at=observed, observed_at=observed,
            provenance='prospective', raw_ref=ref, source_kind='real', content_kind='headline')))
    return n
