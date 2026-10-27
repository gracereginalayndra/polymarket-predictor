import tempfile
import unittest
from pathlib import Path

from src.agents.llm_client import validate_output, LLMClient
from src.agents.orchestrator import context_for
from scripts.run_demo import demo_config


class AgentTests(unittest.TestCase):
    def test_hallucinated_citation(self):
        with self.assertRaises(ValueError):
            validate_output({'probability':.5,'evidence_ids':['fake'],'rationale':'ok','flags':[]}, [])

    def test_probability_validation(self):
        for value in [True,float('nan'),2]:
            with self.assertRaises(ValueError):
                validate_output({'probability':value,'evidence_ids':[],'rationale':'ok','flags':[]},[])

    def test_context_excludes_outcome_market(self):
        context=context_for({'question':'q','rules':'r','cutoff':1,'outcome':1,'market_price':.9},[])
        self.assertNotIn('outcome',context)
        self.assertNotIn('market_price',context)

    def test_mock_cannot_run_as_real(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=demo_config(d);cfg['mode']='prospective'
            with self.assertRaises(ValueError):
                LLMClient(cfg)

    def test_cache_budget_and_replicates(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=demo_config(d);cfg['llm']['max_calls_per_run']=2
            client=LLMClient(cfg)
            context={'question':'q','rules':'r','cutoff':1,'documents':[]}
            first=client.predict('prompt',context,'test')
            second=client.predict('prompt',context,'test')
            self.assertEqual(first,second)
            self.assertEqual(client.calls,1)
            client.predict('prompt',context,'test',replicate=1)
            with self.assertRaises(RuntimeError):
                client.predict('prompt',context,'test',replicate=2)

    def test_synthetic_signal_sentence_punctuation(self):
        result=LLMClient._mock({'question':'q','documents':[{'body':'SYNTHETIC_SIGNAL=0.42.', 'document_id':'x'}]},'news_agent',0)
        self.assertTrue(0 <= result['probability'] <= 1)
