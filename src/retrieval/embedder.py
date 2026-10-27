"""Stateless sparse embeddings: no fitting vocabulary/IDF on future documents."""
from sklearn.feature_extraction.text import HashingVectorizer


def embedder():
    return HashingVectorizer(n_features=2**18, alternate_sign=False, norm='l2',
                             ngram_range=(1, 2), stop_words='english')
