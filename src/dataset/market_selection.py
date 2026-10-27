import re


def exclusion_reason(metadata, price, filters):
    if filters['require_open'] and not metadata['is_open']:
        return 'market_not_open_asof'
    if filters['categories'] and metadata['category'] not in filters['categories']:
        return 'category'
    if (metadata['liquidity'] or 0) < filters['min_liquidity']:
        return 'liquidity'
    if (metadata['volume'] or 0) < filters['min_volume']:
        return 'volume'
    if not filters['min_price'] <= price <= filters['max_price']:
        return 'price_range'
    if any(re.search(p, metadata['question']) for p in filters['exclude_question_patterns']):
        return 'question_pattern'
    return None
