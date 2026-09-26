import copy
import unittest

from claim_verifier.config import DEFAULT
from claim_verifier.footer import presentation_message, render_footer


class FooterTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(DEFAULT["footer"])

    def audit(self, result="PASS", claims=None, **extra):
        return {"result": result, "claims": claims or [], "level": "receipts", "enforcement": "report",
                "repair_attempts": 0, "max_repair_attempts": 2,
                "claim_model": {"model": "gpt-6-luna", "reasoning_effort": "max", "used": False, "available": True}, **extra}

    def claim(self, status="VERIFIED", kind="TEST_SUCCESS", text="Tests pass.", **extra):
        return {"status": status, "type": kind, "claim": text, "decision": "PASS" if status == "VERIFIED" else "CORRECT",
                "task_required": False, "evidence": None, **extra}

    def test_pass_zero_claims(self):
        self.assertEqual(render_footer(self.audit(), self.config), "✓ Claim Verifier · PASS · 0 claims checked")

    def test_pass_one_and_multiple(self):
        self.assertEqual(render_footer(self.audit(claims=[self.claim()]), self.config), "✓ Claim Verifier · PASS · 1/1 verified")
        self.assertEqual(render_footer(self.audit(claims=[self.claim(), self.claim(kind="BUILD_SUCCESS")]), self.config),
                         "✓ Claim Verifier · PASS · 2/2 verified")

    def test_unverified_and_false(self):
        for status in ("UNVERIFIED", "FALSE"):
            with self.subTest(status=status):
                audit = self.audit("CORRECT", [self.claim(status)])
                self.assertEqual(render_footer(audit, self.config),
                                 f"⚠ Claim Verifier · CORRECT\n\n✗ Tests · {status}\n\nLevel: receipts")

    def test_stale(self):
        audit = self.audit("CORRECT", [self.claim("STALE")])
        self.assertEqual(render_footer(audit, self.config),
                         "◷ Claim Verifier · STALE\n\n◷ Tests · STALE\n  Validation occurred before subsequent code changes.\n\nLevel: receipts")

    def test_inconclusive_and_mixed_order(self):
        inconclusive = self.claim("INCONCLUSIVE", kind="GENERIC_VERIFIED", text="No regressions")
        self.assertEqual(render_footer(self.audit("CORRECT", [inconclusive]), self.config),
                         '⚠ Claim Verifier · CORRECT\n\n△ "No regressions" · INCONCLUSIVE\n\nLevel: receipts')
        claims = [self.claim(), inconclusive, self.claim("UNVERIFIED"), self.claim("STALE"), self.claim("FALSE")]
        self.assertEqual(render_footer(self.audit("CORRECT", claims), self.config),
                         '⚠ Claim Verifier · CORRECT\n\n✗ Tests · FALSE\n◷ Tests · STALE\n  Validation occurred before subsequent code changes.\n✗ Tests · UNVERIFIED\n△ "No regressions" · INCONCLUSIVE\n✓ Tests · VERIFIED\n\nLevel: receipts')

    def test_repair_then_pass_then_disclose(self):
        required = self.claim("UNVERIFIED", task_required=True)
        repair = self.audit("REPAIR", [required], repair_attempts=1)
        self.assertEqual(render_footer(repair, self.config),
                         "↻ Claim Verifier · REPAIR\n\n✗ Tests · UNVERIFIED\n  Required by user task.\n\nLevel: receipts\nRepair attempt: 1/2")
        self.assertEqual(render_footer(self.audit(claims=[self.claim()]), self.config), "✓ Claim Verifier · PASS · 1/1 verified")
        disclose = self.audit("DISCLOSE", [self.claim("FALSE", task_required=True)], repair_attempts=2)
        self.assertEqual(render_footer(disclose, self.config),
                         "⚠ Claim Verifier · DISCLOSE\n\n✗ Tests · FALSE\n  Required by user task.\n\nLevel: receipts\nRepair attempts: 2/2")

    def test_disabled_and_all_styles(self):
        audit = self.audit(claims=[self.claim()])
        self.config["enabled"] = False
        self.assertEqual(render_footer(audit, self.config), "")
        self.config["enabled"] = True
        self.config["style"] = "compact"
        self.assertEqual(render_footer(audit, self.config), "✓ Claim Verifier · PASS · 1/1 verified")
        self.config["style"] = "detailed"
        self.assertEqual(render_footer(audit, self.config), "✓ Claim Verifier · PASS\n\n✓ Tests · VERIFIED\n\nLevel: receipts")
        self.config["style"] = "failures-only"
        self.assertEqual(render_footer(audit, self.config), "")
        self.assertEqual(render_footer(self.audit("CORRECT", [self.claim("UNVERIFIED")]), self.config),
                         "⚠ Claim Verifier\n\n✗ Tests · UNVERIFIED")

    def test_compact_counts_never_hide_inconclusive(self):
        self.config["style"] = "compact"
        audit = self.audit("CORRECT", [self.claim(), self.claim("INCONCLUSIVE", kind="GENERIC_VERIFIED")])
        self.assertEqual(render_footer(audit, self.config), "⚠ Claim Verifier · 1 verified · 1 unsupported")
        self.assertEqual(render_footer(self.audit("CORRECT", [self.claim(), self.claim("STALE")]), self.config),
                         "◷ Claim Verifier · 1 verified · 1 stale")
        self.assertEqual(render_footer(self.audit("REPAIR", [self.claim("UNVERIFIED")], repair_attempts=1), self.config),
                         "↻ Claim Verifier · REPAIR · attempt 1/2")
        self.assertEqual(render_footer(self.audit("DISCLOSE", [self.claim("FALSE")], repair_attempts=2), self.config),
                         "⚠ Claim Verifier · DISCLOSE · attempts 2/2")

    def test_priority_and_truncation(self):
        self.config["max_claims"] = 2
        claims = [self.claim() for _ in range(4)] + [self.claim("FALSE"), self.claim("UNVERIFIED", task_required=True)]
        audit = self.audit("REPAIR", claims, repair_attempts=1)
        self.assertEqual(render_footer(audit, self.config),
                         "↻ Claim Verifier · REPAIR\n\n✗ Tests · UNVERIFIED\n  Required by user task.\n✗ Tests · FALSE\n… 4 more claims in audit ledger\n\nLevel: receipts\nRepair attempt: 1/2")

    def test_evidence_model_and_privacy(self):
        claim = self.claim(evidence={"source": "checked_run", "exit_code": 0, "event_id": "tool-18",
                                     "command": "export API_KEY=secret123", "stdout_summary": "secret123"})
        audit = self.audit(claims=[claim])
        self.config["style"] = "detailed"
        self.assertNotIn("Evidence:", render_footer(audit, self.config))
        self.config["show_evidence"] = True
        self.config["show_model"] = True
        self.assertEqual(render_footer(audit, self.config),
                         "✓ Claim Verifier · PASS\n\n✓ Tests · VERIFIED\n  Evidence: checked_run · exit 0\n\nLevel: receipts")
        audit["claim_model"]["used"] = True
        self.assertEqual(render_footer(audit, self.config),
                         "✓ Claim Verifier · PASS\n\n✓ Tests · VERIFIED\n  Evidence: checked_run · exit 0\n\nLevel: receipts\nClaim extraction: GPT-6 Luna · max")
        self.assertNotIn("secret123", render_footer(audit, self.config))

    def test_raw_claim_is_redacted_and_single_line(self):
        claim = self.claim("INCONCLUSIVE", kind="GENERIC_VERIFIED", text="No regressions\nAPI_KEY=secret123 " + "x" * 200)
        rendered = render_footer(self.audit("CORRECT", [claim]), self.config)
        self.assertNotIn("secret123", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertEqual(rendered.count("\n"), 4)

    def test_delivery_modes_and_contradictory_pass(self):
        clean = self.audit(claims=[self.claim()])
        problem = self.audit("CORRECT", [self.claim("UNVERIFIED")])
        self.assertIsNone(presentation_message(clean, render_footer(clean, self.config), self.config))
        self.assertEqual(presentation_message(problem, render_footer(problem, self.config), self.config), render_footer(problem, self.config))
        self.config["delivery"] = "system-message"
        self.assertEqual(presentation_message(clean, render_footer(clean, self.config), self.config), render_footer(clean, self.config))
        contradictory = self.audit("PASS", [self.claim("INCONCLUSIVE")])
        self.assertNotIn("PASS", render_footer(contradictory, self.config))

    def test_optional_enforcement_and_output_only_evidence(self):
        self.config["style"] = "detailed"
        self.config["show_enforcement"] = True
        self.config["show_evidence"] = True
        audit = self.audit(claims=[self.claim(evidence={"event_id": "tool-18", "strength": "output-only",
                                                       "command": "secret", "stdout_summary": "secret"})])
        self.assertEqual(render_footer(audit, self.config),
                         "✓ Claim Verifier · PASS\n\n✓ Tests · VERIFIED\n  Evidence: PostToolUse event tool-18 · output only\n\nLevel: receipts\nEnforcement: report")
        self.assertNotIn("secret", render_footer(audit, self.config))


if __name__ == "__main__":
    unittest.main()
