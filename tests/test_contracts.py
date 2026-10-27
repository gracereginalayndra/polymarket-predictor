import json
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO

from scripts.run_demo import demo_config
from src.agents.llm_client import LLMClient
from src.ingestion.data_api import collect_history
from src.db.loaders import connect, add_document


class ContractTests(unittest.TestCase):
    def test_real_chat_adapter_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=demo_config(d);cfg['mode']='prospective'
            cfg['llm'].update(provider='chat_completions',model='fixture-model')
            expected={'probability':.6,'evidence_ids':[],'rationale':'fixture response','flags':[]}
            payload={'model':'fixture-model','choices':[{'message':{'content':json.dumps(expected)}}],
                     'usage':{'prompt_tokens':10,'completion_tokens':10}}
            with patch.dict('os.environ',{'LLM_API_KEY':'TEST_NOT_A_REAL_KEY','LLM_API_BASE':'https://fixture.test/v1'}):
                client=LLMClient(cfg)
                with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(payload).encode())) as opener:
                    output=client.predict('prompt',{'question':'q','documents':[]},'fixture')
                    self.assertEqual(output['probability'],.6)
                    request=opener.call_args.args[0]
                    self.assertEqual(request.full_url,'https://fixture.test/v1/chat/completions')

    def test_repeated_history_cursor_refused(self):
        class Fake:
            def get(self,*args,**kwargs):
                return {'data':[],'pagination':{'next_cursor':'same','has_more':True}},100,'ref'
        with tempfile.TemporaryDirectory() as d:
            cfg=demo_config(d)
            with self.assertRaises(ValueError):
                collect_history(Fake(),None,cfg,{'market_id':'x','yes_token':'y'},1,20)

    def test_document_first_observation_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            con=connect(d+'/db.sqlite')
            doc=dict(url='https://a.test/a',title='one',body='version1',source='a.test',source_type='news',
                published_at=1,available_at=10,observed_at=10,provenance='prospective',raw_ref='ref',
                source_kind='real',content_kind='article')
            self.assertTrue(add_document(con,doc))
            self.assertFalse(add_document(con,{**doc,'observed_at':20,'available_at':20}))
            self.assertEqual(con.execute('SELECT available_at FROM documents').fetchone()[0],10)
            self.assertTrue(add_document(con,{**doc,'body':'version2','observed_at':20,'available_at':20}))
            self.assertEqual(con.execute('SELECT COUNT(*) FROM documents').fetchone()[0],2)
            con.close()
