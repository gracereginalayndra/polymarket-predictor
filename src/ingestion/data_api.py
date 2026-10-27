"""Data v2 history, cursor validation, settlement exclusion, final labels."""
from src.common import digest, probability, timestamp
from src.db.loaders import insert


def normalize_history(payload, market_id, observed, ref, start, end):
    if not isinstance(payload.get('data'), list):
        raise ValueError('Data v2 history schema changed')
    records = []
    for row in payload['data']:
        grain = int(row['resolution_seconds'])
        t = timestamp(row['timestamp'])
        # Settlement points may be shifted/clamped by API; never use as forecasts.
        if grain <= 0 or not start <= t < end:
            continue
        record = dict(market_id=market_id, timestamp=t, available_at=observed,
                      observed_at=observed, price=probability(row['price']),
                      price_kind='history_unspecified', resolution_seconds=grain,
                      bid=None, ask=None, provenance='retrospective_unverified', raw_ref=ref)
        record['price_id'] = digest(record)
        records.append(record)
    return records


def collect_history(client, con, cfg, market, start, end):
    total = 0
    # v2 bounds explicit windows to 15 days; use nonoverlapping windows.
    for left in range(start, end, 15 * 86400):
        right = min(end, left + 15 * 86400)
        cursor, seen = None, set()
        for _ in range(100):
            params = {'token_id': market['yes_token'], 'start': left, 'end': right, 'cursor': cursor}
            payload, observed, ref = client.get(cfg['polymarket']['data_base'] + '/prices-history', params)
            for record in normalize_history(payload, market['market_id'], observed, ref, left, right):
                total += int(insert(con, 'prices', record))
            paging = payload.get('pagination', {})
            cursor = paging.get('next_cursor')
            if not cursor:
                if paging.get('has_more'):
                    raise ValueError('Pagination claims more data without cursor')
                break
            if cursor in seen:
                raise ValueError('Repeated cursor; refusing infinite pagination')
            seen.add(cursor)
        else:
            raise ValueError('History exceeded 100-page safety limit')
    return total


def collect_resolution(client, con, cfg, market):
    payload, observed, ref = client.get(cfg['polymarket']['data_base'] + '/resolutions',
                                         {'condition': market['condition_id']})
    for row in payload['data']:
        if row.get('condition_id') != market['condition_id']:
            continue
        if str(row.get('status', '')).upper() not in ('RESOLVED', 'SETTLED', 'FINAL'):
            continue
        payouts = row.get('payouts')
        if not isinstance(payouts, list) or len(payouts) != 2:
            raise ValueError('Missing binary payout array; manual resolution review needed')
        p = [float(v) for v in payouts]
        if sorted(p) != [0.0, 1.0]:
            raise ValueError('Voided/split resolution excluded from binary evaluation')
        resolved = timestamp(row['resolved_at'])
        record = dict(market_id=market['market_id'], outcome=int(p[market['yes_index']]),
                      resolved_at=resolved, label_available_at=observed, observed_at=observed,
                      source='polymarket_data_v2', status='final', raw_ref=ref)
        # Rechecking an existing label must agree, but does not change first observation.
        old = con.execute('SELECT outcome FROM resolutions WHERE market_id=?', (market['market_id'],)).fetchone()
        if old:
            if old['outcome'] != record['outcome']:
                raise ValueError('Resolution changed: quarantine and review')
            return 0
        return int(insert(con, 'resolutions', record))
    return 0
