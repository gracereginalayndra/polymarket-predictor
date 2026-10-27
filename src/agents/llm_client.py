"""Provider-neutral chat-completions client; explicit synthetic backend for tests only."""
import json
import os
import re
import urllib.request
from pathlib import Path

import numpy as np

from src.common import canonical, digest, probability, read_json, utcnow, write_json, load_env


def validate_output(result, evidence_ids):
    if not isinstance(result, dict):
        raise ValueError('LLM output must be a JSON object')
    p = probability(result['probability'])
    cited = result.get('evidence_ids')
    if not isinstance(cited, list) or not all(isinstance(x, str) for x in cited):
        raise ValueError('evidence_ids must be a string list')
    if not set(cited).issubset(set(evidence_ids)):
        raise ValueError('Invented or unavailable citation')
    if not isinstance(result.get('rationale'), str) or not result['rationale'].strip():
        raise ValueError('Missing rationale')
    if not isinstance(result.get('flags'), list) or not all(isinstance(x, str) for x in result['flags']):
        raise ValueError('Invalid flags')
    return {**result, 'probability': p}


class LLMClient:
    def __init__(self, cfg):
        load_env()
        self.settings = cfg['llm']
        self.provider = self.settings['provider']
        self.model = self.settings.get('model') or os.getenv('LLM_MODEL')
        self.base = os.getenv('LLM_API_BASE', '').rstrip('/')
        self.key = os.getenv('LLM_API_KEY', '')
        self.calls = 0
        self.cache_hits = 0
        self.cache_dir = Path(cfg['data_dir'])/'cache'/'llm'
        if self.provider == 'mock':
            if cfg['mode'] != 'synthetic' or self.model != 'synthetic-test-backend':
                raise ValueError('Mock backend only allowed in explicitly synthetic experiments')
        elif self.provider == 'chat_completions':
            if not self.key or not self.model or not self.base.startswith('https://') or '.example' in self.base:
                raise ValueError('Set LLM_API_KEY, LLM_API_BASE and LLM_MODEL in .env before real runs')
        else:
            raise ValueError('Unsupported LLM provider')

    def predict(self, prompt, context, role, replicate=0):
        request = dict(model=self.model, temperature=self.settings['temperature'],
                       max_tokens=self.settings['max_output_tokens'],
                       messages=[{'role': 'system', 'content': prompt},
                                 {'role': 'user', 'content': canonical(context)}])
        # Replicates deliberately bypass one another's cache even at temperature=0.
        key = digest({'provider': self.provider, 'base': self.base, 'request': request,
                      'role': role, 'replicate': replicate})
        cache_file = self.cache_dir/(key+'.json')
        if cache_file.exists():
            cached = read_json(cache_file)
            if cached['request_hash'] != key:
                raise ValueError('Cache identity mismatch')
            result = cached['result']
            self.cache_hits += 1
        else:
            if self.calls >= self.settings['max_calls_per_run']:
                raise RuntimeError('Configured LLM call budget exhausted; increase explicitly or resume')
            self.calls += 1
            if self.provider == 'mock':
                result = self._mock(context, role, replicate)
                usage = {'synthetic': True}
                response_model = self.model
            else:
                req = urllib.request.Request(self.base+'/chat/completions', data=canonical(request).encode(),
                    headers={'Authorization': 'Bearer '+self.key, 'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req, timeout=self.settings['timeout_seconds']) as response:
                    payload = json.load(response)
                content = payload['choices'][0]['message']['content']
                # Permit a JSON fence, but never silently extract arbitrary substrings.
                if content.strip().startswith('```'):
                    content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip())
                result = json.loads(content)
                usage, response_model = payload.get('usage', {}), payload.get('model', self.model)
            result = validate_output(result, [d['document_id'] for d in context['documents']])
            write_json(cache_file, {'request_hash': key, 'request': request, 'result': result,
                                   'generated_at': utcnow(), 'response_model': response_model, 'usage': usage})
        result = validate_output(result, [d['document_id'] for d in context['documents']])
        return {**result, 'cache_key': key, 'backend': self.provider}

    @staticmethod
    def _mock(context, role, replicate):
        """No labels or market price are accessible. Synthetic text contains noisy signals."""
        docs = context['documents']
        signals = []
        for doc in docs:
            match = re.search(r'SYNTHETIC_SIGNAL=([0-9]+(?:\.[0-9]+)?)', doc['body'])
            if match:
                signals.append(float(match.group(1)))
        center = float(np.mean(signals)) if signals else 0.5
        jitter = (int(digest([context['question'], role, replicate])[:8], 16)/0xffffffff-0.5)*0.10
        if role == 'verifier' and context.get('drafts'):
            center = 0.5*center+0.5*np.mean([d['probability'] for d in context['drafts']])
        return dict(probability=float(np.clip(center+jitter, .02, .98)),
                    evidence_ids=[d['document_id'] for d in docs[:2]],
                    rationale='SYNTHETIC TEST OUTPUT: deterministic noisy text-signal calculation; not LLM research evidence.',
                    flags=['synthetic_only'])
