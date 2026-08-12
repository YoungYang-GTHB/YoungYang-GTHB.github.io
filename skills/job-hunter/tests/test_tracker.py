import csv
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.tracker import ApplicationTracker


class ApplicationTrackerTests(unittest.TestCase):
    def test_application_id_is_idempotent_across_daily_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            records_dir = Path(temp_dir)
            old_file = records_dir / "2026-08-09.csv"
            with old_file.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "timestamp",
                        "application_id",
                        "company",
                        "position",
                        "status",
                        "url",
                        "location",
                        "resume_version",
                        "notes",
                    ]
                )
                writer.writerow(
                    [
                        "2026-08-09T12:00:00",
                        "robot-role-1",
                        "示例机器人",
                        "具身智能算法工程师",
                        "applied",
                        "https://jobs.example/1",
                        "深圳",
                        "public/resume.pdf",
                        "",
                    ]
                )

            tracker = ApplicationTracker(str(records_dir))
            created = tracker.log(
                "示例机器人",
                "具身智能算法工程师",
                "applied",
                application_id="robot-role-1",
            )

            self.assertFalse(created)
            self.assertEqual(len(list(records_dir.glob("*.csv"))), 1)


if __name__ == "__main__":
    unittest.main()
