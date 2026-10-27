import numpy as np

from src.baselines.single_agent_rag import forecast as single


def forecast(client, context, cfg):
    predictions = [single(client, context, cfg, i) for i in range(cfg['llm']['k'])]
    return dict(probability=float(np.mean([p['probability'] for p in predictions])),
                evidence_ids=sorted({d for p in predictions for d in p['evidence_ids']}),
                rationale='Arithmetic mean of repeated single-agent calls.', flags=[], members=predictions)
