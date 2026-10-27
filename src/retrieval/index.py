"""SQLite is the evidence index; eligibility is resolved before text scoring."""
from src.db.loaders import rows


def eligible_documents(con, cutoff, lookback_days, source_kind, include_social=True):
    records = rows(con, '''SELECT * FROM documents WHERE available_at<=? AND published_at<=?
        AND available_at>=? AND source_kind=?
        AND provenance IN ('prospective','archive_verified','synthetic')
        ORDER BY available_at DESC,document_id''',
        (cutoff, cutoff, cutoff-lookback_days*86400, source_kind))
    return [r for r in records if include_social or r['source_type'] != 'social']
