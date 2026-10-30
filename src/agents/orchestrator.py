"""Frozen evidence, independent first-stage agents, bounded verification, immutable logging."""
from pathlib import Path

from src.agents import news_agent, base_rate_agent, verifier
from src.agents.llm_client import LLMClient
from src.baselines import llm_no_retrieval, single_agent_rag, single_agent_kx
from src.common import canonical, digest, timestamp, utcnow, write_json, source_fingerprint, runtime_info
from src.dataset.leakage_checks import check_evidence
from src.db.loaders import insert, event
from src.retrieval.temporal_retriever import retrieve
from src.retrieval.relevance import require_relevant_evidence

SYSTEMS = ['news_agent', 'base_rate_agent', 'llm_no_retrieval', 'single_agent_rag',
           'single_agent_kx', 'multi_unverified', 'multi_verified', 'multi_no_social']


def context_for(snapshot, docs):
    # Deliberate allowlist: neither labels nor market prices reach any independent agent.
    return dict(question=snapshot['question'], rules=snapshot['rules'], cutoff=int(snapshot['cutoff']),
        documents=[{k: d[k] for k in ('document_id', 'title', 'body', 'published_at', 'available_at',
                                      'source', 'source_type', 'content_kind')} for d in docs])


def run_agents(con, data, cfg):
    if data.empty:
        raise ValueError('No snapshots to forecast')
    kinds = set(data.source_kind)
    if len(kinds) != 1 or (cfg['mode'] == 'synthetic') != (kinds == {'synthetic'}):
        raise ValueError('Mixed or mismatched source kind')
    client = LLMClient(cfg)
    prompt_hash = digest({p.name: p.read_text() for p in sorted(Path(cfg['llm']['prompt_dir']).glob('*.md'))})
    code_hash = source_fingerprint()
    run_id = digest([cfg, client.model, client.base, prompt_hash, code_hash])
    existing = con.execute('SELECT run_id FROM forecast_runs WHERE run_id=?', (run_id,)).fetchone()
    if not existing:
        insert(con, 'forecast_runs', dict(run_id=run_id, created_at=utcnow(), config_json=canonical(cfg),
            config_hash=digest(cfg), model=client.model, provider=client.provider,
            prompt_hash=prompt_hash, source_kind=next(iter(kinds))))
        write_json(Path(cfg['artifact_dir'])/run_id[:12]/'run_metadata.json',
            {'run_id': run_id, 'code_hash': code_hash, 'prompt_hash': prompt_hash,
             'config_hash': digest(cfg), 'runtime': runtime_info(), 'created_at': utcnow()})
    failures = []
    for snapshot in data.to_dict('records'):
        finished = con.execute('SELECT COUNT(*) FROM forecasts WHERE run_id=? AND snapshot_id=? AND status=?',
                               (run_id, snapshot['snapshot_id'], 'ok')).fetchone()[0]
        if finished == len(SYSTEMS):
            continue
        cutoff = int(snapshot['cutoff'])
        docs = retrieve(con, snapshot, cfg)
        no_social_docs = retrieve(con, snapshot, cfg, include_social=False)
        check_evidence(docs, cutoff, snapshot['source_kind'])
        context = context_for(snapshot, docs)
        context_ns = context_for(snapshot, no_social_docs)
        outputs = {}
        # Cache reuses successful API calls on resume. Failed forecast rows are logged
        # to pipeline_events, not permanently installed as a completed forecast.
        def save(system, result, evidence):
            record = dict(forecast_id=digest([run_id, snapshot['snapshot_id'], system]), run_id=run_id,
                snapshot_id=snapshot['snapshot_id'], system=system, probability=result['probability'],
                status='ok', result_json=canonical(result), evidence_json=canonical([d['document_id'] for d in evidence]),
                generated_at=utcnow())
            if not con.execute('SELECT 1 FROM forecasts WHERE forecast_id=?', (record['forecast_id'],)).fetchone():
                insert(con, 'forecasts', record)
        try:
            require_relevant_evidence(snapshot, docs)
            if snapshot['source_kind'] != 'synthetic':
                age = utcnow()-cutoff
                if age > cfg['llm'].get('max_forecast_delay_seconds', 900):
                    frozen = cfg['llm'].get('model_frozen_before')
                    if not cfg['llm']['allow_retrospective'] or not frozen or timestamp(frozen) > cutoff:
                        raise ValueError('Historical LLM run refused: need verified frozen model predating cutoff and explicit retrospective mode')
                known = con.execute('SELECT 1 FROM resolutions WHERE market_id=? AND resolved_at<=?',
                                    (snapshot['market_id'], utcnow())).fetchone()
                if known and not cfg['llm']['allow_retrospective']:
                    raise ValueError('Outcome already resolved before forecast generation')
            outputs['news_agent'] = news_agent.forecast(client, context, cfg)
            outputs['base_rate_agent'] = base_rate_agent.forecast(client, context, cfg)
            outputs['llm_no_retrieval'] = llm_no_retrieval.forecast(client, context, cfg)
            outputs['single_agent_rag'] = single_agent_rag.forecast(client, context, cfg)
            outputs['single_agent_kx'] = single_agent_kx.forecast(client, context, cfg)
            drafts = [outputs['news_agent'], outputs['base_rate_agent']]
            outputs['multi_unverified'] = dict(probability=sum(d['probability'] for d in drafts)/2,
                evidence_ids=outputs['news_agent']['evidence_ids'], rationale='Equal-weight independent agent mean.', flags=[])
            outputs['multi_verified'] = verifier.forecast(client, context, drafts, cfg)
            news_ns = news_agent.forecast(client, context_ns, cfg)
            outputs['multi_no_social'] = verifier.forecast(client, context_ns,
                [news_ns, outputs['base_rate_agent']], cfg)
        except Exception as exc:
            failure = dict(snapshot_id=snapshot['snapshot_id'], error=type(exc).__name__+': '+str(exc))
            failures.append(failure)
            event(con, 'agents', 'failed', failure)
        for system, output in outputs.items():
            evidence = [] if system in ('base_rate_agent', 'llm_no_retrieval') else (no_social_docs if system == 'multi_no_social' else docs)
            save(system, output, evidence)
    return dict(run_id=run_id, calls=client.calls, cache_hits=client.cache_hits, failures=failures)
