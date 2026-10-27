"""Interpretable evidence coverage features, not invented sentiment signals."""


def text_features(documents, cutoff):
    return {'evidence_count': len(documents),
            'unique_sources': len({d['source'] for d in documents}),
            'social_count': sum(d['source_type'] == 'social' for d in documents),
            'mean_evidence_age_hours': sum((cutoff-d['available_at'])/3600 for d in documents)/max(len(documents), 1)}
