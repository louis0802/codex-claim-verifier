import json
import os
import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claim_verifier.claims import extract
from claim_verifier.config import load
from claim_verifier.hook import handle
from claim_verifier.store import ledger
from claim_verifier.verify import command_kind


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {
            "CODEX_HOME": str(self.root / "codex"),
            "PLUGIN_DATA": str(self.root / "data"),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        (self.root / "codex").mkdir()
        self.session = "test-session"

    def config(self, level, enforcement="block", budget=2):
        (self.root / "codex" / "claim-verifier.toml").write_text(
            f'[claim_verifier]\nlevel = "{level}"\nenforcement = "{enforcement}"\nmax_repair_attempts = {budget}\n'
        )

    def payload(self, **items):
        return {"session_id": self.session, "cwd": str(self.root), "turn_id": "turn-1", **items}

    def prompt(self, text):
        return handle("prompt", self.payload(prompt=text))

    def tool(self, name, command, result, event_id="tool-1"):
        return handle("tool", self.payload(tool_name=name, tool_use_id=event_id,
                                           tool_input={"command": command}, tool_response=result))

    def stop(self, text, semantic=None):
        kwargs = {"semantic_normalize": semantic} if semantic else {}
        return handle("stop", self.payload(last_assistant_message=text), **kwargs)

    def audit(self):
        with ledger(self.session) as state:
            return state["audits"][-1]

    def test_a_receipts_unrun_test_can_be_corrected(self):
        self.config("receipts")
        self.prompt("Fix the issue.")
        first = self.stop("Tests pass.")
        self.assertEqual(first["decision"], "block")
        self.assertEqual(self.audit()["claims"][0]["status"], "UNVERIFIED")
        self.assertIsNone(self.stop("I did not run tests."))
        self.assertEqual(self.audit()["result"], "PASS")

    def test_b_required_test_cannot_be_removed(self):
        self.config("complete")
        self.prompt("Fix the issue and run the tests.")
        result = self.stop("I did not run tests.")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(self.audit()["result"], "REPAIR")
        self.assertTrue(self.audit()["claims"][0]["task_required"])

    def test_c_test_becomes_stale_after_write(self):
        self.config("fresh")
        self.tool("Bash", "pytest", {"exit_code": 0, "output": "3 passed"})
        self.tool("apply_patch", "*** Update File: src/a.py\n+new", {"output": "Success"}, "tool-2")
        result = self.stop("All tests pass.")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(self.audit()["claims"][0]["status"], "STALE")

    def test_d_unrequested_push_corrects_without_pushing(self):
        self.config("complete")
        self.prompt("Explain the bug.")
        with patch("subprocess.run", wraps=__import__("subprocess").run) as run:
            result = self.stop("I pushed the branch.")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(self.audit()["result"], "CORRECT")
        self.assertFalse(any(call.args[0][:2] == ["git", "push"] for call in run.call_args_list))

    def test_e_requested_push_repairs_without_pushing(self):
        self.config("complete")
        self.prompt("Commit and push the changes.")
        result = self.stop("Done.")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(self.audit()["result"], "REPAIR")
        self.assertTrue(any(c["type"] == "GIT_PUSH_COMPLETED" for c in self.audit()["claims"]))

    def test_f_luna_normalizes_but_does_not_verify(self):
        self.config("verify")
        sentence = "The serialization contract remains compatible."
        calls = []
        def model(task, sentences, config):
            calls.append((task, sentences, config["model"]))
            return [{"type": "COMPATIBILITY_VERIFICATION", "text": sentence}], True
        self.prompt("Fix serialization without breaking consumers.")
        self.stop(sentence, semantic=model)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.audit()["claims"][0]["status"], "INCONCLUSIVE")

    def test_g_luna_failure_is_inconclusive(self):
        self.config("verify")
        self.stop("The implementation remains compatible.", semantic=lambda *args: ([], False))
        self.assertEqual(self.audit()["claims"][0]["status"], "INCONCLUSIVE")
        self.assertFalse(self.audit()["claim_model"]["available"])

    def test_luna_omission_is_inconclusive(self):
        self.config("verify")
        self.stop("The implementation remains compatible.", semantic=lambda *args: ([], True))
        self.assertEqual(self.audit()["claims"][0]["status"], "INCONCLUSIVE")

    def test_h_budget_exhaustion_discloses(self):
        self.config("complete", budget=2)
        self.prompt("Run the tests.")
        self.assertEqual(self.stop("Done.")["decision"], "block")
        self.assertEqual(self.stop("Done.")["decision"], "block")
        last = self.stop("Done.")
        self.assertIn("systemMessage", last)
        self.assertEqual(self.audit()["result"], "DISCLOSE")

    def test_next_task_resets_required_work_and_budget(self):
        self.config("complete", budget=1)
        self.prompt("Run the tests.")
        self.stop("Done.")
        self.stop("Done.")
        self.prompt("Explain this bug.")
        self.assertIsNone(self.stop("The bug is in input parsing."))
        with ledger(self.session) as state:
            self.assertEqual(state["repair_attempts"], 0)
        self.assertEqual(self.audit()["result"], "PASS")

    def test_failed_test_does_not_back_success(self):
        self.config("verify")
        self.tool("Bash", "pytest", {"exit_code": 1, "output": "1 failed"})
        self.stop("Tests pass.")
        self.assertEqual(self.audit()["claims"][0]["status"], "FALSE")

    def test_compound_shell_does_not_count_as_test(self):
        self.assertIsNone(command_kind("echo pytest && true"))
        self.assertIsNone(command_kind("cat > script.sh <<EOF\npytest\nEOF"))
        self.assertEqual(command_kind("dotnet test"), "TEST_SUCCESS")

    def test_file_claim_requires_path_evidence(self):
        self.config("verify")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("new\n")
        self.tool("apply_patch", "*** Update File: src/a.py\n+new", {"output": "Success"})
        self.stop("I updated src/a.py.")
        self.assertEqual(self.audit()["claims"][0]["status"], "VERIFIED")

    def test_project_override_requires_trust(self):
        self.config("verify", enforcement="report")
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "claim-verifier.toml").write_text('[claim_verifier]\nlevel = "strict"\n')
        self.assertEqual(load(str(self.root))["level"], "verify")
        path = str(self.root).replace('\\', '\\\\').replace('"', '\\"')
        (self.root / "codex" / "config.toml").write_text(f'[projects."{path}"]\ntrust_level = "trusted"\n')
        self.assertEqual(load(str(self.root))["level"], "strict")

    def test_receipts_output_only_is_weaker_than_verify(self):
        self.config("receipts")
        self.tool("Bash", "pytest", {"output": "2 passed"})
        self.stop("Tests pass.")
        self.assertEqual(self.audit()["claims"][0]["status"], "VERIFIED")
        self.config("verify")
        self.stop("Tests pass.")
        self.assertEqual(self.audit()["claims"][0]["status"], "INCONCLUSIVE")

    def test_negated_clause_does_not_hide_later_success_claim(self):
        claims, _ = extract("I did not run tests but tests pass.")
        self.assertEqual([claim["type"] for claim in claims], ["TEST_SUCCESS"])

    def test_checked_run_makes_real_exit_status_available(self):
        self.config("verify")
        (self.root / "Makefile").write_text("test:\n\t@echo '2 passed'\n")
        helper = Path(__file__).resolve().parents[1] / "scripts" / "checked_run.py"
        copied_helper = self.root / "checked_run.py"
        shutil.copyfile(helper, copied_helper)
        shutil.copytree(helper.parents[1] / "claim_verifier", self.root / "claim_verifier")
        command = f"python3 {copied_helper} -- make test"
        result = subprocess.run(["python3", str(copied_helper), "--", "make", "test"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("CLAIM_VERIFIER_RECEIPT:", result.stdout)
        self.tool("Bash", command, result.stdout)
        self.stop("Tests pass.")
        self.assertEqual(self.audit()["claims"][0]["status"], "VERIFIED")

    def test_checked_run_rejects_remote_mutation(self):
        helper = Path(__file__).resolve().parents[1] / "scripts" / "checked_run.py"
        result = subprocess.run(["python3", str(helper), "--", "git", "push"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("CLAIM_VERIFIER_RECEIPT:", result.stdout)

    def test_report_footer_is_stored_and_problem_is_emitted(self):
        self.config("receipts", enforcement="report")
        result = self.stop("Tests pass.")
        self.assertEqual(result, {"systemMessage": "⚠ Claim Verifier · CORRECT\n\n✗ Tests · UNVERIFIED\n\nLevel: receipts"})
        self.assertEqual(self.audit()["footer"]["rendered"], result["systemMessage"])
        self.assertEqual(self.audit()["footer"]["channel"], "systemMessage")
        self.assertIsNone(self.stop("I did not run tests."))
        self.assertEqual(self.audit()["footer"]["rendered"], "✓ Claim Verifier · PASS · 0 claims checked")
        self.assertEqual(self.audit()["footer"]["channel"], "none")

    def test_system_message_can_emit_pass_without_blocking(self):
        self.config("receipts", enforcement="report")
        with (self.root / "codex" / "claim-verifier.toml").open("a") as stream:
            stream.write('[claim_verifier.footer]\ndelivery = "system-message"\n')
        self.assertEqual(self.stop("Done."), {"systemMessage": "✓ Claim Verifier · PASS · 0 claims checked"})

    def test_warn_forces_detailed_problem_receipt(self):
        self.config("verify", enforcement="warn")
        with (self.root / "codex" / "claim-verifier.toml").open("a") as stream:
            stream.write('[claim_verifier.footer]\nstyle = "compact"\n')
        result = self.stop("Tests pass.")
        self.assertEqual(result, {"systemMessage": "⚠ Claim Verifier · CORRECT\n\n✗ Tests · UNVERIFIED\n\nLevel: verify"})
        self.assertEqual(self.audit()["footer"]["style"], "detailed")

    def test_repair_receipt_replaced_by_pass_after_evidence(self):
        self.config("complete", enforcement="block")
        self.prompt("Run the tests.")
        first = self.stop("Done.")
        self.assertEqual(first["decision"], "block")
        self.assertIn("↻ Claim Verifier · REPAIR", first["reason"])
        self.assertEqual(self.audit()["footer"]["channel"], "continuation-reason")
        self.tool("Bash", "pytest", {"exit_code": 0, "output": "3 passed"})
        self.assertIsNone(self.stop("Tests pass."))
        self.assertEqual(self.audit()["result"], "PASS")
        self.assertEqual(self.audit()["footer"]["rendered"], "✓ Claim Verifier · PASS · 1/1 verified")

    def test_exhausted_repair_footer_never_passes(self):
        self.config("complete", enforcement="block", budget=1)
        self.prompt("Run the tests.")
        self.stop("Done.")
        final = self.stop("Done.")
        self.assertIn("⚠ Claim Verifier · DISCLOSE", final["systemMessage"])
        self.assertEqual(self.audit()["footer"]["channel"], "systemMessage")
        self.assertNotIn("PASS", self.audit()["footer"]["rendered"])

    def test_footer_config_validates_and_project_overrides(self):
        self.config("receipts", enforcement="report")
        global_file = self.root / "codex" / "claim-verifier.toml"
        with global_file.open("a") as stream:
            stream.write('[claim_verifier.footer]\nstyle = "compact"\nmax_claims = 3\n')
        self.assertEqual(load(str(self.root))["footer"]["style"], "compact")
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "claim-verifier.toml").write_text('[claim_verifier.footer]\nstyle = "detailed"\n')
        path = str(self.root).replace('\\', '\\\\').replace('"', '\\"')
        (self.root / "codex" / "config.toml").write_text(f'[projects."{path}"]\ntrust_level = "trusted"\n')
        self.assertEqual(load(str(self.root))["footer"]["style"], "detailed")
        self.assertEqual(load(str(self.root))["footer"]["max_claims"], 3)
        (self.root / ".codex" / "claim-verifier.toml").write_text('[claim_verifier.footer]\ndelivery = "native"\n')
        with self.assertRaisesRegex(ValueError, "unsupported footer delivery"):
            load(str(self.root))

    def test_disabled_footer_keeps_verification_without_receipt(self):
        self.config("receipts", enforcement="report")
        with (self.root / "codex" / "claim-verifier.toml").open("a") as stream:
            stream.write('[claim_verifier.footer]\nenabled = false\n')
        self.assertIsNone(self.stop("Tests pass."))
        self.assertEqual(self.audit()["result"], "CORRECT")
        self.assertNotIn("footer", self.audit())


if __name__ == "__main__":
    unittest.main()
