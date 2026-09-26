import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claim_verifier.diagnostics import (RECEIPT_VISIBILITY, SMOKE_MARKER, doctor_status, latest_audit,
                                        latest_session, read_ledgers, record_desktop_observation,
                                        summarize_session)
from claim_verifier.hook import handle
from claim_verifier.store import ledger


ROOT = Path(__file__).resolve().parents[1]


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.codex = self.root / "codex"
        self.codex.mkdir()
        self.data = self.root / "data"
        self.env = patch.dict(os.environ, {"CODEX_HOME": str(self.codex), "PLUGIN_DATA": str(self.data),
                                        "PLUGIN_ROOT": str(ROOT)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def payload(self, session="session-one", **extra):
        return {"session_id": session, "turn_id": "turn-one", "cwd": str(self.root), **extra}

    def test_heartbeat_and_marker_do_not_change_decision(self):
        handle("prompt", self.payload(prompt=f"{SMOKE_MARKER}\nDo not run tests."))
        handle("tool", self.payload(tool_name="Read", tool_use_id="read-1", tool_input={"path": "README.md"},
                                    tool_response={"content": "hello"}))
        response = handle("stop", self.payload(last_assistant_message="Tests pass."))
        self.assertIn("systemMessage", response)
        with ledger("session-one") as state:
            runtime = state["runtime"]
            self.assertEqual(runtime["diagnostic_tag"], "desktop-smoke")
            self.assertEqual(runtime["hook_events_seen"], ["UserPromptSubmit", "PostToolUse", "Stop"])
            self.assertEqual([beat["hook"] for beat in runtime["heartbeats"]], runtime["hook_events_seen"])
            self.assertTrue(runtime["heartbeats"][-1]["audit_created"])
            self.assertEqual(runtime["heartbeats"][1]["tool"], "Read")
            self.assertTrue(runtime["plugin_root_present"])
            self.assertTrue(runtime["plugin_data_present"])
            self.assertEqual(state["audits"][-1]["claims"][0]["status"], "UNVERIFIED")
            self.assertEqual(state["audits"][-1]["claims"][0]["decision"], "CORRECT")

    def test_partial_missing_and_no_desktop_inference(self):
        self.assertEqual(summarize_session(None)["observation"], "NOT OBSERVED")
        handle("prompt", self.payload(prompt=SMOKE_MARKER))
        summary = summarize_session(latest_session(read_ledgers(), tagged=True))
        self.assertEqual(summary["observation"], "INCONCLUSIVE")
        self.assertFalse(summary["audit_created"])
        self.assertEqual(summary["hook_events_seen"], ["UserPromptSubmit"])
        status = doctor_status(str(self.root))
        self.assertEqual(status["tagged_smoke_session"]["observation"], "INCONCLUSIVE")
        self.assertEqual(status["desktop"]["hook_support"], "INCONCLUSIVE")
        self.assertEqual(status["hook_trust"], "UNKNOWN")

    def test_latest_audit_skips_new_prompt_only_session(self):
        handle("stop", self.payload(session="older", last_assistant_message="Done."))
        handle("prompt", self.payload(session="newer", prompt=SMOKE_MARKER))
        self.assertEqual(latest_session(read_ledgers())["session_id"], "newer")
        self.assertEqual(latest_audit()["session_id"], "older")
        self.assertIsNone(latest_audit(tagged=True))

    def test_tagged_prompt_does_not_relabel_prior_audit_in_same_session(self):
        handle("stop", self.payload(last_assistant_message="Done."))
        handle("prompt", self.payload(prompt=SMOKE_MARKER))
        self.assertIsNone(latest_audit(tagged=True))
        summary = summarize_session(latest_session(read_ledgers(), tagged=True))
        self.assertEqual(summary["hook_events_seen"], ["UserPromptSubmit"])
        self.assertFalse(summary["audit_created"])

    def test_cli_output_and_missing_session(self):
        handle("prompt", self.payload(session="", prompt=SMOKE_MARKER))
        handle("stop", self.payload(last_assistant_message="Tests pass."))
        doctor = subprocess.run([sys.executable, str(ROOT / "scripts" / "doctor.py"), "--json"],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        status = json.loads(doctor.stdout)
        self.assertEqual(status["recent_session"]["observation"], "INCONCLUSIVE")
        audit = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit.py"), "latest"],
                               capture_output=True, text=True, cwd=self.root)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        self.assertIn("UNVERIFIED", audit.stdout)
        self.assertIn("Stop", audit.stdout)

    def test_runtime_does_not_copy_prompt_or_tool_output(self):
        secret = "SECRET_SAMPLE_DO_NOT_STORE"
        handle("prompt", self.payload(prompt=f"{SMOKE_MARKER}\n{secret}"))
        handle("tool", self.payload(tool_name="Bash", tool_use_id="one", tool_input={"command": "echo hello"},
                                    tool_response={"output": secret}))
        with ledger("session-one") as state:
            self.assertNotIn(secret, json.dumps(state["runtime"]))

    def test_operator_provenance_never_creates_hook_evidence(self):
        self.assertIn("AUDIT_ONLY", RECEIPT_VISIBILITY)
        with self.assertRaises(ValueError):
            record_desktop_observation("missing", "AUDIT_ONLY")
        handle("prompt", self.payload(prompt=SMOKE_MARKER))
        record = record_desktop_observation("session-one", "AUDIT_ONLY")
        self.assertEqual(record["provenance"], "operator-supplied")
        status = doctor_status(str(self.root))["desktop"]
        self.assertEqual(status["hook_support"], "PARTIAL")
        self.assertEqual(status["receipt_visibility"], "AUDIT_ONLY")
        self.assertFalse(status["all_hooks_and_audit"])
        self.assertFalse(status["checked_run_verified"])

    def test_full_desktop_status_requires_verified_checked_run(self):
        handle("prompt", self.payload(prompt=SMOKE_MARKER))
        handle("tool", self.payload(tool_name="Bash", tool_use_id="tool-1",
                                    tool_input={"command": "pytest"},
                                    tool_response={"output": "1 passed", "exit_code": 0}))
        handle("stop", self.payload(last_assistant_message="Tests pass."))
        record_desktop_observation("session-one", "INCONCLUSIVE")
        self.assertEqual(doctor_status(str(self.root))["desktop"]["hook_support"], "PARTIAL")
        with ledger("session-one") as state:
            state["events"][-1]["checked_run"] = {"kind": "TEST_SUCCESS", "exit_code": 0}
        self.assertEqual(doctor_status(str(self.root))["desktop"]["hook_support"], "FULL")


if __name__ == "__main__":
    unittest.main()
