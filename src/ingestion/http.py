"""Bounded GET client with immutable raw-response archive and visible failures."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from src.common import digest, utcnow, write_json


class HTTPClient:
    def __init__(self, cfg):
        self.settings = cfg['http']
        self.raw_dir = Path(cfg['data_dir']) / 'raw'
        self.last_request = 0.0

    def get(self, url, params=None, json_response=True):
        if urllib.parse.urlsplit(url).scheme != 'https':
            raise ValueError('Only HTTPS source URLs are supported')
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
        full = url + (('?' if '?' not in url else '&') + query if query else '')
        for attempt in range(self.settings['retries'] + 1):
            pause = self.settings['min_interval_seconds'] - (time.monotonic() - self.last_request)
            if pause > 0:
                time.sleep(pause)
            self.last_request = time.monotonic()
            req = urllib.request.Request(full, headers={'User-Agent': self.settings['user_agent']})
            try:
                with urllib.request.urlopen(req, timeout=self.settings['timeout_seconds']) as response:
                    raw = response.read(10_000_001)
                    if len(raw) > 10_000_000:
                        raise ValueError('Source response exceeded 10 MB bound')
                    observed = utcnow()
                    text = raw.decode('utf-8')
                    payload = json.loads(text) if json_response else text
                    ref = self.raw_dir / f"{observed}_{digest([full, text])}.json"
                    write_json(ref, {'url': full, 'observed_at': observed, 'status': response.status,
                                     'payload': payload})
                    return payload, observed, str(ref)
            except urllib.error.HTTPError as exc:
                retryable = exc.code in (429, 500, 502, 503, 504)
                if not retryable or attempt == self.settings['retries']:
                    raise RuntimeError(f'HTTP {exc.code} from {urllib.parse.urlsplit(url).netloc}') from None
                time.sleep(min(2 ** attempt, 4))
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == self.settings['retries']:
                    raise RuntimeError(f'Network failure at {urllib.parse.urlsplit(url).netloc}: {type(exc).__name__}') from None
                time.sleep(min(2 ** attempt, 4))
        raise RuntimeError('Exhausted HTTP retries')
