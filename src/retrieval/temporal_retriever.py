from collections import Counter

from src.dataset.leakage_checks import check_evidence
from src.retrieval.embedder import embedder
from src.retrieval.index import eligible_documents


def retrieve(con, snapshot, cfg, include_social=None):
    settings = cfg['retrieval']
    include_social = settings['include_social'] if include_social is None else include_social
    candidates = eligible_documents(con, int(snapshot['cutoff']), cfg['dataset']['lookback_days'],
                                    snapshot['source_kind'], include_social)
    check_evidence(candidates, snapshot['cutoff'], snapshot['source_kind'])
    if not candidates:
        return []
    vectorizer = embedder()
    query = snapshot['question'] + ' ' + snapshot['rules'][:1200]
    matrix = vectorizer.transform([d['title']+' '+d['body'] for d in candidates])
    scores = (matrix @ vectorizer.transform([query]).T).toarray().ravel()
    chosen, hashes, domains = [], set(), Counter()
    for idx in sorted(range(len(candidates)), key=lambda i: (-scores[i], candidates[i]['document_id'])):
        doc = candidates[idx]
        if scores[idx] < settings['min_score']:
            continue
        if doc['content_hash'] in hashes or domains[doc['source']] >= settings['max_per_domain']:
            continue
        chosen.append({**doc, 'body': doc['body'][:settings['max_chars']], 'retrieval_score': float(scores[idx])})
        hashes.add(doc['content_hash'])
        domains[doc['source']] += 1
        if len(chosen) == settings['top_k']:
            break
    return chosen
