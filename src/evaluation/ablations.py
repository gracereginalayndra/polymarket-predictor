from src.evaluation.stats_tests import paired_cluster_bootstrap

CONTRASTS = [
    ('hybrid_verified', 'market_calibrated', 'Increment over market recalibration'),
    ('hybrid_verified', 'stat_logreg', 'Increment over market features'),
    ('hybrid_verified', 'hybrid_single', 'Increment over single-agent hybrid'),
    ('multi_verified', 'multi_unverified', 'Verification step'),
    ('multi_verified', 'multi_no_social', 'Social evidence'),
    ('single_agent_rag', 'llm_no_retrieval', 'Retrieval plus its prompt specification'),
    ('multi_verified', 'single_agent_kx', 'Agent specialization versus repeated calls'),
]


def contrasts(frame, cfg):
    results = []
    for system, reference, question in CONTRASTS:
        if system in frame and reference in frame:
            results.append({'system': system, 'reference': reference, 'question': question,
                **paired_cluster_bootstrap(frame, system, reference,
                    cfg['evaluation']['bootstrap_samples'], cfg['seed'])})
    return results
