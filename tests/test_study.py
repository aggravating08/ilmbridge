import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import study
from server import Handler

class RetrievalTests(unittest.TestCase):
    def test_relevant_passage_ranks_first(self):
        self.assertEqual(study.retrieve(study.SAMPLE, 'Where does the Calvin cycle take place?')[0]['id'], 3)

    def test_two_stage_question_retrieves_both_stages(self):
        ids = {p['id'] for p in study.retrieve(study.SAMPLE, 'How do light-dependent reactions support the Calvin cycle?')}
        self.assertTrue({2, 3}.issubset(ids))

    def test_unrelated_question_abstains_without_model(self):
        with patch('study.generate') as model:
            result = study.ask(study.SAMPLE, 'Quantum entanglement?', 'ai')
        self.assertEqual(result['mode'], 'no_match'); model.assert_not_called()

    def test_sources_are_exact_substrings(self):
        for p in study.retrieve(study.SAMPLE, 'photosynthesis'):
            self.assertIn(p['text'], study.SAMPLE)

    def test_unicode_retrieval(self):
        self.assertTrue(study.retrieve('پودے روشنی سے خوراک بناتے ہیں۔', 'روشنی'))

    def test_long_input_is_bounded(self):
        self.assertTrue(all(len(p['text']) <= 650 for p in study.chunks('a' * 4000)))

    def test_practice_answers_reconstruct_source(self):
        result = study.practice(study.SAMPLE)
        self.assertEqual(len(result['quiz']), 6)
        for q in result['quiz']:
            self.assertEqual(q['prompt'].replace('______', q['answer']), q['evidence'])
            self.assertIn(q['evidence'], study.SAMPLE)

    def test_empty_practice(self):
        self.assertEqual(study.practice(''), {'cards': [], 'quiz': []})

class FakeResponse:
    def __init__(self, answer): self.answer = answer
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps({'message': {'content': self.answer}, 'prompt_eval_count': 12, 'eval_count': 8}).encode()

class ModelTests(unittest.TestCase):
    def test_valid_model_citations_and_usage(self):
        with patch('urllib.request.urlopen', return_value=FakeResponse('Chlorophyll absorbs sunlight [1].')):
            result = study.ask(study.SAMPLE, 'chlorophyll', 'ai')
        self.assertTrue(result['citations_present']); self.assertEqual(result['usage']['output_tokens'], 8)

    def test_invalid_citation_rejected(self):
        with patch('urllib.request.urlopen', return_value=FakeResponse('A claim [999].')):
            with self.assertRaises(study.ModelUnavailable): study.ask(study.SAMPLE, 'chlorophyll', 'ai')

    def test_unavailable_model_is_not_silently_mocked(self):
        with patch('urllib.request.urlopen', side_effect=OSError('offline')):
            with self.assertRaises(study.ModelUnavailable): study.ask(study.SAMPLE, 'chlorophyll', 'ai')

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def request(self, path, data, origin=None, mime='application/json'):
        headers = {'Content-Type': mime}
        if origin: headers['Origin'] = origin
        request = urllib.request.Request(self.url + path, json.dumps(data).encode(), headers)
        try:
            with urllib.request.urlopen(request) as r: return r.status, json.load(r)
        except urllib.error.HTTPError as e: return e.code, json.load(e)
    def test_search_http_roundtrip(self):
        code, data = self.request('/api/ask', {'text': study.SAMPLE, 'question': 'Calvin cycle', 'mode': 'source'})
        self.assertEqual(code, 200); self.assertEqual(data['sources'][0]['id'], 3)
    def test_short_notes_rejected(self):
        self.assertEqual(self.request('/api/practice', {'text': 'abc'})[0], 400)
    def test_invalid_question_type_rejected(self):
        self.assertEqual(self.request('/api/ask', {'text': study.SAMPLE, 'question': []})[0], 400)
    def test_unsupported_language_rejected(self):
        self.assertEqual(self.request('/api/ask', {'text': study.SAMPLE, 'question': 'Calvin cycle', 'language': 'French'})[0], 400)
    def test_cross_origin_rejected(self):
        self.assertEqual(self.request('/api/practice', {'text': study.SAMPLE}, origin='https://example.com')[0], 403)
    def test_non_json_rejected(self):
        self.assertEqual(self.request('/api/practice', {'text': study.SAMPLE}, mime='text/plain')[0], 415)
    def test_unknown_route(self):
        self.assertEqual(self.request('/missing', {'text': study.SAMPLE})[0], 404)
    def test_security_headers(self):
        with urllib.request.urlopen(self.url) as r:
            self.assertIn("frame-ancestors 'none'", r.headers['Content-Security-Policy'])
            self.assertIn(b'IlmBridge', r.read())

if __name__ == '__main__': unittest.main()
