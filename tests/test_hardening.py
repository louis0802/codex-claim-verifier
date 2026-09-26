import json
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
from claim_verifier.claims import extract
from claim_verifier.diagnostics import latest_audit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_renderer', ROOT / 'scripts/audit.py')
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)

CORPUS = [
    ('Tests pass.', ['TEST_SUCCESS'], []),
    ('Tests passed in an imaginary run.', ['TEST_SUCCESS'], []),
    ('Tests did not pass.', [], []),
    ('I did not run tests.', [], []),
    ('"Tests pass."', ['TEST_SUCCESS'], []),
    ('The requested closing text is not a verified result:', [], []),
    ('I cannot verify that tests passed.', [], []),
    ('The following statement is unverified.', [], []),
    ('Claim Verifier marked this as unsupported.', [], []),
    ('I cannot verify that "Tests pass."', [], []),
    ('Tests pass, but I cannot verify the build.', ['TEST_SUCCESS'], []),
    ('I cannot verify that tests passed; build succeeded.', ['BUILD_SUCCESS'], []),
    ('I cannot verify that tests passed, and lint passed.', ['LINT_SUCCESS'], []),
    ('I verified the changes.', [], ['I verified the changes.']),
    ('The requested closing text is not a verified result: Tests pass.', ['TEST_SUCCESS'], []),
    ('I cannot verify that tests passed, but build succeeded.', ['BUILD_SUCCESS'], []),
]

class HardeningTests(unittest.TestCase):
    def test_extraction_corpus(self):
        for text, types, ambiguous in CORPUS:
            with self.subTest(text=text):
                claims, actual = extract(text)
                self.assertEqual([c['type'] for c in claims], types)
                self.assertEqual(actual, ambiguous)

    def test_audit_preserves_stored_receipt_and_only_selected_fields(self):
        footer = {'style': 'adaptive', 'rendered': '⚠ Stored receipt\n\nLevel: receipts',
                  'delivery': 'auto', 'channel': 'systemMessage', 'raw_hook_output': 'private'}
        state = {'session_id': 'fixture-session', 'runtime': {}, 'audits': [
            {'timestamp': '2026-09-27T00:00:00Z', 'result': 'CORRECT', 'claims': [], 'footer': footer}]}
        with patch('claim_verifier.diagnostics.read_ledgers', return_value=[state]):
            audit = latest_audit()
        self.assertEqual(audit['footer'], {k: footer[k] for k in ('style', 'rendered', 'delivery', 'channel')})
        text = audit_module.render(audit)
        self.assertIn('\nReceipt\n\n' + footer['rendered'], text)
        self.assertIn('systemMessage', text)
        self.assertIn('not confirmed', text)
        self.assertNotIn('private', json.dumps(audit))

    def test_legacy_audit_without_footer(self):
        audit = {'session_id': 'fixture', 'started': None, 'timestamp': None,
                 'diagnostics_available': False, 'result': 'PASS', 'claims': []}
        self.assertIn('Not available for this audit.', audit_module.render(audit))

    def test_stored_only_receipt_does_not_claim_delivery_attempt(self):
        audit = {'session_id': 'fixture', 'started': None, 'timestamp': None,
                 'diagnostics_available': False, 'result': 'PASS', 'claims': [],
                 'footer': {'rendered': 'stored', 'channel': 'none'}}
        text = audit_module.render(audit)
        self.assertIn('Receipt delivery\nstored only', text)
        self.assertNotIn('Delivery attempted', text)
