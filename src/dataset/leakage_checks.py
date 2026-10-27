"""Fail-closed temporal and group checks. Assertions are not used for validation."""


def check_evidence(documents, cutoff, source_kind):
    for doc in documents:
        if doc['source_kind'] != source_kind:
            raise ValueError('Mixed synthetic and real evidence')
        if doc['published_at'] > cutoff or doc['available_at'] > cutoff:
            raise ValueError('Future evidence')
        if doc['provenance'] == 'prospective' and doc['observed_at'] > cutoff:
            raise ValueError('Evidence had not been observed at the cutoff')
        if doc['provenance'] not in ('prospective', 'archive_verified', 'synthetic'):
            raise ValueError('Unverified evidence provenance')


def check_snapshot(snapshot, metadata, price):
    t = snapshot['cutoff']
    if metadata['available_at'] > t or metadata['scheduled_end'] <= t:
        raise ValueError('Future metadata or expired question')
    if price['timestamp'] > t or price['available_at'] > t:
        raise ValueError('Future price')
    if price['resolution_seconds'] <= 0 or price['provenance'] == 'retrospective_unverified':
        raise ValueError('Settlement price or unverified historical observation')
    for item in (metadata, price):
        if item['provenance'] == 'prospective' and item['observed_at'] > t:
            raise ValueError('Not observed at cutoff')


def check_disjoint_groups(train, validation, test):
    sets = [set(f.event_group) for f in (train, validation, test)]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise ValueError('Related events overlap splits')


def check_training_labels(frame, fit_time):
    if frame.empty or frame.outcome.isna().any():
        raise ValueError('Training needs resolved outcomes')
    if (frame.label_available_at > fit_time).any():
        raise ValueError('Training used labels not yet available at fit time')
    if (frame.cutoff >= fit_time).any():
        raise ValueError('Training forecasts must precede fit time')
    if not set(frame.outcome).issubset({0, 1}):
        raise ValueError('Only binary final outcomes supported')
