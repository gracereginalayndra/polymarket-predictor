import math

from src.db.loaders import rows


def market_features(con, market_id, cutoff, price, metadata):
    previous = rows(con, '''SELECT price FROM prices WHERE market_id=? AND timestamp<=?
        AND available_at<=? AND provenance IN ('prospective','archive_verified','synthetic')
        AND resolution_seconds>0 ORDER BY timestamp DESC,available_at DESC LIMIT 1''',
        (market_id, cutoff-86400, cutoff))
    return {
        'price_change_24h': price['price']-previous[0]['price'] if previous else 0.0,
        'missing_history': int(not previous),
        'spread': price['ask']-price['bid'] if price['ask'] is not None and price['bid'] is not None else 0.0,
        'missing_spread': int(price['ask'] is None or price['bid'] is None),
        'log_volume': math.log1p(max(metadata['volume'] or 0, 0)),
        'log_liquidity': math.log1p(max(metadata['liquidity'] or 0, 0)),
        'price_age_seconds': cutoff-price['timestamp'],
    }
