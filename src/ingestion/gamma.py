"""Gamma discovery; never infer historical metadata availability from creation dates."""
import json

from src.common import digest, timestamp
from src.db.loaders import insert, event


def array(value):
    return json.loads(value) if isinstance(value, str) else value


def normalize_market(raw, observed, raw_ref):
    outcomes, tokens = array(raw.get('outcomes', [])), array(raw.get('clobTokenIds', []))
    if not isinstance(outcomes, list) or len(outcomes) != 2 or len(tokens) != 2:
        raise ValueError('Only explicitly mapped two-outcome CTF markets are supported')
    names = [str(s).strip().lower() for s in outcomes]
    if set(names) != {'yes', 'no'}:
        raise ValueError('Nonbinary or non-Yes/No outcome mapping')
    yes = names.index('yes')
    market_id = str(raw['id'])
    events = raw.get('events') or []
    # Missing groups are rejected; treating correlated contracts as independent is unsafe.
    if not events or not events[0].get('id'):
        raise ValueError('Missing event identity: supply reviewed group mapping')
    market = dict(market_id=market_id, condition_id=raw['conditionId'],
                  event_group=str(events[0]['id']), yes_token=str(tokens[yes]),
                  no_token=str(tokens[1-yes]), yes_index=yes, source_kind='real')
    version = dict(market_id=market_id, available_at=observed, observed_at=observed,
                   question=raw['question'], rules=raw.get('description', ''),
                   scheduled_end=timestamp(raw.get('endDate') or raw.get('endDateIso')),
                   category=raw.get('category') or events[0].get('category') or 'unknown',
                   is_open=int(bool(raw.get('active')) and not bool(raw.get('closed'))),
                   liquidity=float(raw.get('liquidityNum') or raw.get('liquidity') or 0),
                   volume=float(raw.get('volumeNum') or raw.get('volume') or 0),
                   provenance='prospective', raw_ref=raw_ref)
    version['version_id'] = digest(version)
    return market, version


def collect(client, con, cfg, closed=False):
    settings = cfg['polymarket']
    count, seen = 0, set()
    for page in range(settings['max_pages']):
        payload, observed, ref = client.get(settings['gamma_base'] + '/markets', {
            'closed': str(closed).lower(), 'limit': settings['page_size'],
            'offset': page * settings['page_size'], 'order': settings.get('discovery_order', 'volume24hr'), 'ascending': 'false'})
        if not isinstance(payload, list):
            raise ValueError('Gamma response schema changed: expected list')
        if not payload:
            break
        for raw in payload:
            if str(raw.get('id')) in seen:
                continue
            seen.add(str(raw.get('id')))
            try:
                market, version = normalize_market(raw, observed, ref)
                overrides = settings.get('group_overrides', {})
                market['event_group'] = str(overrides.get(market['market_id'], market['event_group']))
                insert(con, 'markets', market)
                insert(con, 'market_versions', version)
                count += 1
            except (ValueError, KeyError, TypeError) as exc:
                event(con, 'gamma', 'excluded', {'market_id': str(raw.get('id')), 'reason': str(exc)})
            if count >= settings['max_markets']:
                return count
    return count
