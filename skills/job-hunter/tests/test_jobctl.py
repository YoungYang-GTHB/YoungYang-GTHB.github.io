import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.jobctl import (
    ApplicationLedger,
    LedgerError,
    confirmation_token,
    ensure_submittable,
    render_summary,
)


class JobctlTests(unittest.TestCase):
    def make_application(self):
        return {
            "id": "example-robot-role",
            "company": "示例机器人",
            "program": "提前批",
            "position": "Robot Learning 工程师",
            "job_id": "R001",
            "phase": "提前批",
            "policy_status": "current_year_safe",
            "policy_evidence": "当届公告明确不影响正式批",
            "status": "prepared",
            "deadline": "2026-08-30",
            "job_url": "https://jobs.example/R001",
            "locations": ["深圳", "北京"],
            "resume": "public/resume.pdf",
            "channel": "官网投递",
            "referral_code": "",
            "record_verified": False,
            "notes": "",
        }

    def test_confirmation_token_changes_with_material_fields(self):
        application = self.make_application()
        first = confirmation_token(application)
        application["locations"] = ["上海"]
        second = confirmation_token(application)

        self.assertTrue(first.startswith("CONFIRM:example-robot-role:"))
        self.assertNotEqual(first, second)

    def test_ledger_round_trip_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            summary_path = Path(temp_dir) / "summary.md"
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-10",
                "applications": [self.make_application()],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            ledger = ApplicationLedger(ledger_path)
            self.assertEqual(ledger.validate(), [])
            content = render_summary(ledger, summary_path)

            self.assertIn("Robot Learning 工程师", content)
            self.assertIn("待确认", content)
            self.assertTrue(summary_path.exists())

    def test_submission_gate_enforces_phase_and_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            application = self.make_application()
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-10",
                "applications": [application],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            ledger = ApplicationLedger(ledger_path)

            ensure_submittable(ledger, application)
            application["phase"] = "秋招"
            with self.assertRaises(LedgerError):
                ensure_submittable(ledger, application)
            application["phase"] = "提前批"
            application["policy_status"] = "unknown"
            with self.assertRaises(LedgerError):
                ensure_submittable(ledger, application)


if __name__ == "__main__":
    unittest.main()
