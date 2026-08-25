import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.run_daily_monitor import compare_liepin, run_daily


class DailyMonitorTests(unittest.TestCase):
    def test_compare_liepin_reports_company_and_position_count_changes(self):
        previous = {
            "companies": [
                {"company": "公司A", "liepin_company_id": "1", "open_position_count": 10},
                {"company": "公司B", "liepin_company_id": "2", "open_position_count": 20},
            ]
        }
        current = {
            "companies": [
                {"company": "公司A", "liepin_company_id": "1", "open_position_count": 12},
                {"company": "公司C", "liepin_company_id": "3", "open_position_count": 5},
            ]
        }
        delta = compare_liepin(previous, current)
        self.assertEqual(delta["added_company_count"], 1)
        self.assertEqual(delta["removed_company_count"], 1)
        self.assertEqual(delta["position_count_change_count"], 1)
        self.assertEqual(delta["position_count_changes"][0]["current_open_position_count"], 12)

    @patch("scripts.run_daily_monitor.run_command")
    def test_writes_reminders_and_manifest_when_liepin_succeeds(self, command):
        command.side_effect = [
            {"exit_code": 0, "stdout": "urgent reminders\n", "stderr": "", "command": []},
            {"exit_code": 0, "stdout": "{}\n", "stderr": "", "command": []},
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest, exit_code = run_daily("2026-08-18", output)
            self.assertEqual(exit_code, 0)
            self.assertEqual((output / "2026-08-18-reminders.txt").read_text(), "urgent reminders\n")
            self.assertTrue((output / "2026-08-18-manifest.json").exists())
            self.assertFalse(manifest["application_submission"])
            generated_at = datetime.fromisoformat(manifest["generated_at"])
            self.assertEqual(generated_at.utcoffset(), timedelta(hours=8))

    @patch("scripts.run_daily_monitor.run_command")
    def test_same_day_rerun_preserves_reproducible_liepin_baseline(self, command):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            snapshot = output / "2026-08-18-liepin-hardtech.json"
            snapshot.write_text(
                '{"companies":[{"company":"公司A","liepin_company_id":"1","open_position_count":1}]}',
                encoding="utf-8",
            )

            def run(command_args):
                if "scan_liepin_hardtech.py" in " ".join(command_args):
                    snapshot.write_text(
                        '{"companies":[{"company":"公司A","liepin_company_id":"1","open_position_count":2}]}',
                        encoding="utf-8",
                    )
                    return {"exit_code": 0, "stdout": "", "stderr": "", "command": command_args}
                return {
                    "exit_code": 0,
                    "stdout": "reminders\n",
                    "stderr": "",
                    "command": command_args,
                }

            command.side_effect = run
            manifest, exit_code = run_daily("2026-08-18", output)

            baseline = output / "2026-08-18-liepin-baseline.json"
            delta = output / "2026-08-18-liepin-delta.json"
            self.assertEqual(exit_code, 0)
            self.assertTrue(baseline.exists())
            self.assertIn('"open_position_count": 1', baseline.read_text(encoding="utf-8"))
            self.assertIn('"position_count_change_count": 1', delta.read_text(encoding="utf-8"))
            self.assertEqual(manifest["liepin_discovery"]["delta"], str(delta))
            self.assertIn(str(baseline), delta.read_text(encoding="utf-8"))

    @patch("scripts.run_daily_monitor.run_command")
    def test_preserves_reminders_and_marks_degraded_liepin_run(self, command):
        command.side_effect = [
            {"exit_code": 0, "stdout": "reminders\n", "stderr": "", "command": []},
            {"exit_code": 2, "stdout": "", "stderr": "browser unavailable", "command": []},
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest, exit_code = run_daily("2026-08-18", output)
            self.assertEqual(exit_code, 1)
            self.assertTrue((output / "2026-08-18-reminders.txt").exists())
            self.assertIsNone(manifest["liepin_discovery"]["output"])
            self.assertEqual(manifest["liepin_discovery"]["stderr"], "browser unavailable")

    @patch("scripts.run_daily_monitor.run_command")
    def test_skip_liepin_only_runs_reminders(self, command):
        command.return_value = {
            "exit_code": 0,
            "stdout": "reminders\n",
            "stderr": "",
            "command": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            manifest, exit_code = run_daily("2026-08-18", Path(directory), skip_liepin=True)
            self.assertEqual(exit_code, 0)
            self.assertEqual(command.call_count, 1)
            self.assertTrue(manifest["liepin_discovery"]["skipped"])


if __name__ == "__main__":
    unittest.main()
