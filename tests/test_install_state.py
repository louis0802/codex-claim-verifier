import concurrent.futures
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claim_verifier.hook import handle
from claim_verifier.install_state import EXPECTED, identity, initialize, read_state, state_path
from claim_verifier.store import data_dir

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from public_cli import doctor


class InstallStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'codex'
        self.home.mkdir()
        self.data = self.root / 'runtime-data'
        env = patch.dict(os.environ, {'CODEX_HOME': str(self.home), 'PLUGIN_DATA': str(self.data)})
        env.start()
        self.addCleanup(env.stop)
        (self.home / 'claim-verifier.toml').write_text('[claim_verifier]\nlevel = "receipts"\nenforcement = "report"\n')
        self.version = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())['version']
        self.installation = {'installed': True, 'enabled': True, 'version': self.version, 'root': str(ROOT)}
        data_dir()
        initialize(ROOT, self.version, self.data)

    def event(self, event, session='test'):
        payload = {'session_id': session, 'cwd': str(self.root), 'prompt': 'Read a file.',
                   'tool_name': 'Read', 'tool_use_id': 'read-1', 'tool_input': {'path': 'README.md'},
                   'tool_response': {'content': 'hello'}, 'last_assistant_message': 'Hello.'}
        return handle(event, payload)

    def test_no_activity_then_three_successful_hooks_and_audit(self):
        self.assertFalse(read_state()['ready'])
        self.assertEqual(doctor(self.installation)['exit_code'], 1)
        self.event('prompt')
        self.assertEqual(read_state()['hook_activity'], 'OBSERVED')
        self.assertFalse(read_state()['ready'])
        self.event('tool')
        self.assertFalse(read_state()['ready'])
        self.event('stop')
        state = read_state()
        self.assertTrue(state['ready'])
        self.assertEqual(state['hooks_seen'], list(EXPECTED))
        self.assertEqual(state['hook_trust'], 'UNKNOWN')
        self.assertEqual(doctor(self.installation)['exit_code'], 0)
        self.assertEqual(stat.S_IMODE(state_path().stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.data.stat().st_mode), 0o700)
        for file in self.data.glob('*.json'):
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)

    def test_missing_session_and_unknown_event_do_not_qualify(self):
        self.event('prompt', session='')
        self.event('other')
        self.assertEqual(read_state()['hook_activity'], 'NOT_OBSERVED')
        self.assertFalse(read_state()['ready'])

    def test_exception_cannot_mark_hook_or_audit_success(self):
        with patch('claim_verifier.hook.load', side_effect=ValueError('broken')):
            with self.assertRaises(ValueError):
                self.event('stop')
        self.assertFalse(read_state()['ready'])
        self.assertEqual(read_state()['hooks_seen'], [])

    def test_disabled_verifier_observes_hooks_but_no_audit_or_ready(self):
        (self.home / 'claim-verifier.toml').write_text('[claim_verifier]\nenabled = false\n')
        for event in ('prompt', 'tool', 'stop'):
            self.event(event)
        self.assertEqual(read_state()['hooks_seen'], list(EXPECTED))
        self.assertFalse(read_state()['audit_created'])
        self.assertFalse(read_state()['ready'])
        self.assertEqual(doctor(self.installation)['status'], 'ATTENTION REQUIRED')

    def test_upgrade_invalidates_and_old_hook_cannot_restore_activity(self):
        for event in ('prompt', 'tool', 'stop'):
            self.event(event)
        self.assertTrue(read_state()['ready'])
        with patch('claim_verifier.install_state.identity', return_value='new-package'):
            initialize(ROOT, 'new-version', self.data)
        before = read_state()
        self.event('prompt')
        self.assertEqual(read_state(), before)
        self.assertEqual(before['hook_activity'], 'NOT_OBSERVED')
        self.assertFalse(before['ready'])
        self.assertEqual(doctor(self.installation)['exit_code'], 1)

    def test_reinitialize_preserves_activity_and_state_timestamp(self):
        self.event('prompt')
        before = read_state()
        stamp = state_path().stat().st_mtime_ns
        initialize(ROOT, self.version, self.data)
        self.assertEqual(read_state(), before)
        self.assertEqual(state_path().stat().st_mtime_ns, stamp)

    def test_audit_deleted_cannot_make_doctor_ready(self):
        for event in ('prompt', 'tool', 'stop'):
            self.event(event)
        for file in self.data.glob('*.json'):
            file.unlink()
        self.assertEqual(doctor(self.installation)['exit_code'], 1)
        self.assertFalse(doctor(self.installation)['audit_generation'])
        self.assertEqual(doctor(self.installation)['status'], 'WAITING FOR AUDIT')

    def test_audit_reader_deduplicates_equivalent_data_paths(self):
        from claim_verifier.diagnostics import read_ledgers
        self.event('stop')
        with patch('claim_verifier.diagnostics.data_roots', return_value=[self.data, self.data / '..' / self.data.name]):
            self.assertEqual(len(read_ledgers()), 1)

    def test_diagnostics_find_actual_plugin_data_without_environment(self):
        for event in ('prompt', 'tool', 'stop'):
            self.event(event)
        with patch.dict(os.environ):
            os.environ.pop('PLUGIN_DATA', None)
            self.assertEqual(doctor(self.installation)['exit_code'], 0)

    def test_node_and_python_package_identity_match(self):
        script = 'import {identity} from "./cli/system.mjs"; console.log(identity(process.cwd()));'
        result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), identity(ROOT))

    def test_parallel_sessions_do_not_lose_hook_observations(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.event, event, session=event) for event in ('prompt', 'tool', 'stop')]
            for future in futures:
                future.result()
        self.assertTrue(read_state()['ready'])

    def test_invalid_state_and_config_fail_closed(self):
        state_path().write_text('not json')
        self.assertEqual(doctor(self.installation)['exit_code'], 2)
        state_path().unlink()
        (self.home / 'claim-verifier.toml').write_text('[claim_verifier]\nlevel = "invalid"\n')
        self.assertEqual(doctor(self.installation)['exit_code'], 2)

    def test_state_is_separate_and_does_not_touch_trust_records(self):
        trust = self.home / 'hooks-trust.json'
        trust.write_text('human review sentinel')
        for event in ('prompt', 'tool', 'stop'):
            self.event(event)
        self.assertEqual(trust.read_text(), 'human review sentinel')
        self.assertFalse((self.data / 'claim-verifier-installation.json').exists())


if __name__ == '__main__':
    unittest.main()
