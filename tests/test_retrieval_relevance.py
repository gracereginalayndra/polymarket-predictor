import tempfile
import unittest
from unittest.mock import patch
from scripts.run_demo import demo_config, populate
from src.db.loaders import connect
from src.dataset.snapshots import build, frame
from src.agents.orchestrator import run_agents
from src.retrieval.relevance import rejection_reason, relevance_profile
from src.retrieval.temporal_retriever import retrieve

QUESTIONS = [f'Will the {p} Party control the House after the 2026 Midterm elections?' for p in ('Democratic', 'Republican')]
BAD = ["Netanyahu's bloc leading Israel election but short of majority, partial results show", 'Agencies seek comment on proposed third-party risk management guidance and issue statement on community bank engagement with core service providers', 'Minutes of the Federal Open Market Committee, September 15-16, 2026', 'How could Israel break election deadlock? Here are four scenarios']

def doc(title, body='', available=10):
    return dict(document_id=title, content_hash=title, title=title, body=body, source='example.test', source_type='news', content_kind='article', published_at=10, available_at=available, observed_at=available, provenance='prospective', source_kind='real')

class RelevanceTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = dict(question=QUESTIONS[0], rules='Federal Reserve Netanyahu election majority', cutoff=100, source_kind='real')
        self.cfg = dict(retrieval=dict(include_social=True, top_k=8, min_score=.01, max_per_domain=8, max_chars=1800), dataset=dict(lookback_days=30))
    def test_reported_headlines_rejected_for_both_parties(self):
        for question in QUESTIONS:
            for title in BAD:
                with self.subTest(question=question, title=title):
                    self.assertIsNotNone(rejection_reason({**self.snapshot, 'question': question}, doc(title)))
    def test_house_election_positive_examples(self):
        for title in ['Democrats lead polling for 2026 House elections', 'GOP seeks House majority in midterms', 'U.S. House election forecast shifts after new polls', 'Republicans defend House seats in competitive races']:
            self.assertIsNone(rejection_reason(self.snapshot, doc(title)))
    def test_wrong_country_chamber_or_topic(self):
        for title in ['Philippines House of Representatives election results', 'Republicans lead Senate election polls', 'U.S. housing prices rise', 'U.S. House cafeteria menu announced']:
            self.assertIsNotNone(rejection_reason(self.snapshot, doc(title)))
    def test_explicit_other_election_cycle(self):
        self.assertIsNotNone(rejection_reason(self.snapshot, doc('2024 House elections: Republicans win majority')))
    def test_relevant_body_can_supply_context(self):
        self.assertIsNone(rejection_reason(self.snapshot, doc('New polling released', 'Democrats lead Republicans in the race for the House majority.')))
    def test_end_to_end_empty_instead_of_wrong_documents(self):
        with patch('src.retrieval.temporal_retriever.eligible_documents', return_value=[doc(t) for t in BAD]):
            self.assertEqual(retrieve(None, self.snapshot, self.cfg), [])
    def test_positive_survives_ranking_with_distractors(self):
        relevant = doc('Democratic Party leads 2026 House elections polling')
        with patch('src.retrieval.temporal_retriever.eligible_documents', return_value=[doc(t) for t in BAD]+[relevant]):
            self.assertEqual([d['title'] for d in retrieve(None, self.snapshot, self.cfg)], [relevant['title']])
    def test_hidden_body_text_cannot_qualify(self):
        with patch('src.retrieval.temporal_retriever.eligible_documents', return_value=[doc('Unrelated topic', 'x '*1000 + 'Democrats lead House election polls')]):
            self.assertEqual(retrieve(None, self.snapshot, self.cfg), [])
    def test_future_document_still_rejected(self):
        with patch('src.retrieval.temporal_retriever.eligible_documents', return_value=[doc('Democrats lead House elections', available=101)]):
            with self.assertRaisesRegex(ValueError, 'Future evidence'):
                retrieve(None, self.snapshot, self.cfg)
    def test_unrelated_market_not_claimed_supported(self):
        self.assertIsNone(relevance_profile({'question': 'Will the Fed cut interest rates?'}))
    def test_missing_evidence_skips_all_llm_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = demo_config(tmp); con = connect(cfg['database'])
            try:
                populate(con, cfg, groups=1); build(con, cfg)
                data = frame(con).head(1).copy(); data['question'] = QUESTIONS[0]
                with patch('src.agents.orchestrator.retrieve', return_value=[]), patch('src.agents.llm_client.LLMClient.predict') as predict:
                    result = run_agents(con, data, cfg); predict.assert_not_called()
                self.assertEqual(result['calls'], 0)
                self.assertIn('insufficient_relevant_evidence', result['failures'][0]['error'])
                self.assertEqual(con.execute('SELECT COUNT(*) FROM forecasts').fetchone()[0], 0)
            finally:
                con.close()
