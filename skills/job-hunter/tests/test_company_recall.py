import argparse
import copy
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.company_recall import build_company_review_queue, merge_company_review_queue
from scripts.exclusions import ExclusionStore
from scripts.fetch_jobs import JobFilter, fetch_navigation, run_fetch
from scripts.jobctl import cmd_shortlist


class CompanyRecallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.exclusions = ExclusionStore(Path(self.tmp.name) / "excluded.yaml")
        self.filter = JobFilter({"filters": {
            "industries": ["机器人"], "graduation_year": "2027",
            "matching": {"primary_keywords": ["VLA", "机器人"]},
        }}, phase="秋招")

    def build(self, rows, recent=()):
        return build_company_review_queue(rows, self.filter, self.exclusions, recent)

    def test_low_score_missing_or_unrelated_industry_remains_unknown(self):
        rows = [{"企业名称": "甲公司", "职位": "市场", "行业": "零售", "毕业年份": "2026"},
                {"企业名称": "乙公司", "职位": "营销"}]
        before = copy.deepcopy(rows)
        result = self.build(rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(rows, before)
        for company in result:
            self.assertEqual(company["review_status"], "pending_official_review")
            self.assertFalse(company["application_authorized"])
            self.assertEqual(company["eligibility"], "unknown")

    def test_company_and_job_exclusions_are_separate(self):
        self.exclusions.data["exclusions"] = [
            {"id": "company-stop", "company": "甲公司", "reason": "本人放弃"},
            {"id": "job-stop", "company": "乙公司", "position_keyword": "博士", "reason": "官方学历不符"},
        ]
        result = {x["company"]: x for x in self.build([
            {"企业名称": "甲公司", "职位": "VLA"},
            {"企业名称": "乙公司", "职位": "博士研究员"},
            {"企业名称": "乙公司", "职位": "招聘公告"},
        ])}
        self.assertEqual(result["甲公司"]["review_status"], "held_company_exclusion")
        self.assertEqual(result["乙公司"]["review_status"], "pending_official_review")
        self.assertEqual(result["乙公司"]["excluded_job_rule_ids"], ["job-stop"])

    def test_shared_urls_do_not_merge_companies_or_expose_query_secrets(self):
        result = self.build([
            {"企业名称": name, "投递地址": "https://example.org/jobs?token=secret#private"}
            for name in ("甲公司", "乙公司")
        ])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(x["lead_urls"] == ["https://example.org/jobs"] for x in result))

    def test_recent_history_is_hold_not_new_application_recommendation(self):
        result = self.build([{"企业名称": "甲公司"}], recent=["甲公司"])[0]
        self.assertEqual(result["review_status"], "held_history_review")
        self.assertTrue(result["history_check_required"])

    def test_seen_records_and_applied_url_still_recall_company(self):
        api, state, tracker = mock.Mock(), mock.Mock(), mock.Mock()
        api.fetch_jobs.return_value = {"data": [{"企业名称": "甲公司", "职位": "营销",
                                               "投递地址": "https://example.org/jobs"}],
                                      "pagination": {"total_rows": 1, "has_next": False}}
        state.get_cutoff.return_value = None
        state.has_seen_record_history.return_value = True
        state.is_seen_record.return_value = True
        state.is_applied.return_value = True
        tracker.get_recent_companies.return_value = []
        result = fetch_navigation(api=api, state=state, tracker=tracker,
                                  job_filter=self.filter, exclusions=self.exclusions,
                                  nav={"id": 71, "name": "秋招"}, dry_run=True)
        self.assertEqual(result["records"], [])
        self.assertEqual(result["company_reviews"][0]["company"], "甲公司")
        state.remember_records.assert_not_called()
        state.update.assert_not_called()

    def test_cross_source_same_name_keeps_provenance_and_writes_sidecar(self):
        company = self.build([{"企业名称": "甲公司"}])[0]
        results = [dict(nav={"id": n, "name": str(n)}, fetched=1, deduped=0,
                        excluded=0, matched=0, records=[], mode="FULL", total_rows=1,
                        company_reviews=[company]) for n in (70, 71)]
        config = {"navigations": [x["nav"] for x in results],
                  "output": {"directory": self.tmp.name}}
        with mock.patch("scripts.fetch_jobs.OfferAPI"), mock.patch("scripts.fetch_jobs.FetcherState"), \
             mock.patch("scripts.fetch_jobs.ApplicationTracker"), mock.patch("scripts.fetch_jobs.ExclusionStore", return_value=self.exclusions), \
             mock.patch("scripts.fetch_jobs.fetch_navigation", side_effect=results):
            run_fetch(config, force_full=True, phase="秋招")
        files = list(Path(self.tmp.name).glob("*-companies.jsonl"))
        self.assertEqual(len(files), 1)
        output = [json.loads(line) for line in files[0].read_text().splitlines()]
        self.assertEqual([x["source_navigation_id"] for x in output], [70, 71])
        self.assertTrue(all(x["company"] == "甲公司" for x in output))
        stable = Path(self.tmp.name) / "company-review-autumn.jsonl"
        self.assertEqual(len(stable.read_text().splitlines()), 2)

    def test_company_shortlist_ignores_keyword_cutoff(self):
        path = Path(self.tmp.name) / "companies.jsonl"
        path.write_text(json.dumps(self.build([{"企业名称": "甲公司"}])[0]) + "\n")
        args = argparse.Namespace(phase="秋招", input=str(path), companies=True,
                                  limit=0, min_score=100, json=True, ledger="unused")
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(cmd_shortlist(args), 0)
        self.assertEqual(json.loads(output.getvalue())[0]["company"], "甲公司")

    def test_generic_ai_and_rl_do_not_claim_embodied_role(self):
        for title in ("AI金融Agent", "强化学习多模态算法", "RL engineer",
                      "多模态大模型", "视频世界模型", "模仿学习算法"):
            with self.subTest(title=title):
                filt = JobFilter({"filters": {"matching": {
                    "primary_keywords": ["强化学习", "多模态", "模仿学习"]}}})
                self.assertEqual(filt.classify_track(title), "AI/多模态待核")
        for title in ("具身智能", "VLA后训练", "机器人学习", "世界动作模型",
                      "Robot Learning Engineer", "Embodied AI"):
            with self.subTest(title=title):
                self.assertEqual(self.filter.classify_track(title), "具身智能")

    def test_phase_unknown_and_unverified_identity_are_not_hard_excluded(self):
        result = self.build([{"企业名称": "甲公司", "招聘批次": "未知",
                              "_company_identity_source": "announcement_title_unverified"}])[0]
        self.assertEqual(result["review_status"], "pending_official_review")
        self.assertFalse(result["company_identity_verified"])
        self.assertEqual(result["identity_sources"], ["announcement_title_unverified"])

    def test_full_then_incremental_keeps_old_companies_and_refreshes_exclusions(self):
        original = [dict(x, source_navigation_id=71, coverage_mode="FULL")
                    for x in self.build([{"企业名称": "甲公司"}, {"企业名称": "乙公司"}])]
        full = merge_company_review_queue([], original, self.exclusions, observed_at="2026-09-12")
        self.exclusions.data["exclusions"] = [{"id": "new-hold", "company": "甲公司"}]
        new = [dict(x, source_navigation_id=71, coverage_mode="INCR")
               for x in self.build([{"企业名称": "丙公司"}])]
        merged = merge_company_review_queue(full, new, self.exclusions, observed_at="2026-09-13")
        by_name = {x["company"]: x for x in merged}
        self.assertEqual(len(merged), 3)
        self.assertEqual(by_name["甲公司"]["review_status"], "held_company_exclusion")
        self.assertFalse(by_name["乙公司"]["seen_in_current_fetch"])
        self.assertEqual(by_name["乙公司"]["last_seen_at"], "2026-09-12")
        self.assertTrue(by_name["丙公司"]["seen_in_current_fetch"])
        self.assertTrue(all(x["job_exclusions_check_required"] for x in merged))
        self.exclusions.data["exclusions"] = []
        refreshed = merge_company_review_queue(merged, [], self.exclusions)
        self.assertEqual(next(x for x in refreshed if x["company"] == "甲公司")["review_status"],
                         "pending_official_review")


if __name__ == "__main__":
    unittest.main()
