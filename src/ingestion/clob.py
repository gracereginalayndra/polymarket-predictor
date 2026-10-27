"""Current quotes and explicit legacy history adapter. No trading endpoints."""
from src.common import digest, probability
from src.db.loaders import insert


def quote_from_book(payload):
    bids = [probability(x['price']) for x in payload.get('bids', []) if float(x['size']) > 0]
    asks = [probability(x['price']) for x in payload.get('asks', []) if float(x['size']) > 0]
    if not bids or not asks:
        raise ValueError('One-sided or empty order book')
    bid, ask = max(bids), min(asks)
    if bid > ask:
        raise ValueError('Crossed order book')
    return bid, ask, (bid + ask) / 2


def collect_quote(client, con, cfg, market):
    payload, observed, ref = client.get(cfg['polymarket']['clob_base'] + '/book',
                                         {'token_id': market['yes_token']})
    bid, ask, price = quote_from_book(payload)
    record = dict(market_id=market['market_id'], timestamp=observed,
                  available_at=observed, observed_at=observed, price=price,
                  price_kind='midpoint', resolution_seconds=1, bid=bid, ask=ask,
                  provenance='prospective', raw_ref=ref)
    record['price_id'] = digest(record)
    insert(con, 'prices', record)
    return record


def legacy_history(client, con, cfg, market, start, end):
    payload, observed, ref = client.get(cfg['polymarket']['clob_base'] + '/prices-history',
        {'market': market['yes_token'], 'startTs': start, 'endTs': end, 'fidelity': 60})
    if not isinstance(payload.get('history'), list):
        raise ValueError('Legacy CLOB history schema changed')
    n = 0
    for row in payload['history']:
        t = int(row['t'])
        if not start <= t < end:
            continue
        record = dict(market_id=market['market_id'], timestamp=t, available_at=observed,
                      observed_at=observed, price=probability(row['p']), price_kind='history_unspecified',
                      resolution_seconds=3600, bid=None, ask=None,
                      provenance='retrospective_unverified', raw_ref=ref)
        record['price_id'] = digest(record)
        insert(con, 'prices', record)
        n += 1
    return n
