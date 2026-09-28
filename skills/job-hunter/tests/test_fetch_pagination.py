import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.fetch_jobs import fetch_navigation
from scripts.jobctl import build_parser, cmd_scan, cmd_sync


class FetchPaginationTests(unittest.TestCase):
    def fetch(self, cutoff=None, force_full=False, anomaly=False):
        api = mock.Mock()
        api.fetch_jobs.side_effect = [
            {"data": [{"更新时间": "2026-09-09", "id": str(i)}],
             "pagination": {"total_rows": 3, "has_next": i < 3}}
            for i in range(1, 4)
        ]
        state = mock.Mock()
        state.get_cutoff.return_value = cutoff
        state.check_count_anomaly.return_value = anomaly
        state.has_seen_record_history.return_value = False
        state.is_applied.return_value = False
        tracker = mock.Mock()
        tracker.get_recent_companies.return_value = []
        exclusions = mock.Mock()
        exclusions.match.return_value = None
        job_filter = mock.Mock(_phase="秋招")
        job_filter.passes.return_value = True
        job_filter.score.return_value = 1
        with mock.patch("scripts.fetch_jobs.normalize_platform_record", side_effect=lambda r, n: r):
            result = fetch_navigation(api=api, state=state, job_filter=job_filter,
                                      tracker=tracker, exclusions=exclusions,
                                      nav={"id": 71, "name": "秋招汇总"},
                                      max_records=1, force_full=force_full, dry_run=True)
        state.update.assert_not_called()
        return result, api

    def test_all_full_modes_ignore_source_budget(self):
        for kwargs in ({}, {"cutoff": "2026-09-01", "force_full": True},
                       {"cutoff": "2026-09-01", "anomaly": True}):
            with self.subTest(kwargs=kwargs):
                result, api = self.fetch(**kwargs)
                self.assertEqual(result["fetched"], 3)
                self.assertEqual(api.fetch_jobs.call_count, 3)

    def test_incremental_retains_budget(self):
        result, api = self.fetch(cutoff="2026-09-01")
        self.assertEqual(result["fetched"], 1)
        self.assertEqual(api.fetch_jobs.call_count, 1)

    def test_nav_default_delegates_to_fetch_config_and_explicit_override_survives(self):
        for name, handler in (("scan", cmd_scan), ("sync", cmd_sync)):
            for explicit in (False, True):
                argv = [name, "--phase", "秋招"] + (["--nav", "71"] if explicit else [])
                args = build_parser().parse_args(argv)
                self.assertEqual(args.nav, 71 if explicit else None)
                with mock.patch("scripts.jobctl.subprocess.run", return_value=mock.Mock(returncode=0)) as run, \
                     mock.patch("scripts.jobctl.cmd_shortlist", return_value=0):
                    self.assertEqual(handler(args), 0)
                command = run.call_args.args[0]
                self.assertEqual("--nav" in command, explicit)
                if explicit:
                    self.assertEqual(command[command.index("--nav") + 1], "71")


if __name__ == "__main__":
    unittest.main()
