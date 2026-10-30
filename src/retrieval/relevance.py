"""Conservative, auditable topic gate for US House-control questions.

This is a scoped lexical gate, not a semantic relevance guarantee. Other topics
retain the original retrieval behaviour and require their own reviewed profiles.
"""
import re


def matches(pattern, text):
    return re.search(pattern, text, re.IGNORECASE) is not None


def relevance_profile(snapshot):
    q = snapshot['question']
    house = matches(r'\bhouse\b', q)
    control = matches(r'\b(control|majority|win)\b', q)
    us_context = matches(r'\b(democratic|republican|democrats|republicans|gop|midterms?|united states)\b|\bu\.?s\.?\b', q)
    return 'us_house_control' if house and control and us_context else None


def rejection_reason(snapshot, document):
    if relevance_profile(snapshot) is None:
        return None
    title = document['title']
    # Inspect only the text actually sent to the agent, not hidden/truncated text.
    text = title + ' ' + document['body']
    explicit_house = matches(r'\b(?:u\.?s\.?|united states|american)\s+house\b', text)
    chamber = matches(r'\bhouse(?:\s+of\s+representatives)?\b', text)
    us_context = matches(r'\b(democrats?|democratic|republicans?|gop|united states|american)\b|\bu\.?s\.?\b', text)
    electoral = matches(r'\b(elections?|midterms?|polls?|polling|ballot|seats?|majority|control|races?|campaigns?)\b', text)
    if not (explicit_house or (chamber and us_context)):
        return 'missing_us_house_context'
    if not electoral:
        return 'missing_election_context'
    target_years = set(re.findall(r'\b20\d{2}\b', snapshot['question']))
    headline_cycles = set(re.findall(
        r'\b(20\d{2})\s+(?:(?:us|u\.s\.|american|congressional|house|midterm)\s+){0,3}elections?\b',
        title, re.IGNORECASE))
    if target_years and headline_cycles and not target_years.intersection(headline_cycles):
        return 'different_headline_election_year'
    return None


def require_relevant_evidence(snapshot, documents):
    if relevance_profile(snapshot) and not documents:
        raise ValueError('insufficient_relevant_evidence: no eligible US House election evidence; no LLM calls made for this snapshot')
