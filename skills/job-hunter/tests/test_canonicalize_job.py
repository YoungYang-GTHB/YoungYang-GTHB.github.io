import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.canonicalize_job import (
    canonical_company_key,
    canonical_url,
    load_company_aliases,
    job_version,
    logical_job_key,
)


class CanonicalizeJobTests(unittest.TestCase):
    def test_aliases_map_brand_and_full_name_to_one_company(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "aliases.yaml"
            source.write_text(
                """schema_version: 1\ncompanies:\n  - id: agibot\n    canonical_name: 智元机器人\n    aliases: [AGIBOT, 智元机器人 AGIBOT]\n""",
                encoding="utf-8",
            )
            aliases = load_company_aliases(source)
        self.assertEqual(canonical_company_key("AGIBOT", aliases), "agibot")
        self.assertEqual(canonical_company_key("智元机器人（AGIBOT）", aliases), "agibot")

    def test_unknown_legal_entities_are_not_aggressively_merged(self):
        self.assertNotEqual(canonical_company_key("示例科技有限公司"), canonical_company_key("示例科技集团"))

    def test_url_drops_tracking_but_keeps_job_identity_and_spa_route(self):
        left = canonical_url(
            "https://Jobs.Example.com/campus?jobId=42&recommendCode=ABC&utm_source=x#/jobs/42?shareId=1"
        )
        right = canonical_url("https://jobs.example.com/campus?jobId=42#/jobs/42")
        self.assertEqual(left, right)
        self.assertIn("jobId=42", left)
        self.assertIn("#/jobs/42", left)

    def test_official_job_id_is_stable_across_referral_urls(self):
        values = {
            "company_key": "agibot",
            "program": "2027校招",
            "phase": "秋招",
            "official_job_id": "J-42",
            "title": "VLA算法工程师",
        }
        first = logical_job_key(**values, official_url="https://example/jobs/42?token=a")
        second = logical_job_key(**values, official_url="https://example/jobs/42?token=b")
        self.assertEqual(first, second)

    def test_job_version_is_canonical_and_changes_with_material_fields(self):
        base = {
            "job_key": "job-example",
            "status": "online",
            "locations": ["苏州", "杭州"],
            "updated_at": "2026-09-07",
        }
        first = job_version(
            **base,
            jd={"requirements": ["Python"], "duties": ["部署"]},
        )
        reordered = job_version(
            **{**base, "locations": ["杭州", "苏州"]},
            jd={"duties": ["部署"], "requirements": ["Python"]},
        )
        changed = job_version(
            **base,
            jd={"requirements": ["Python", "强化学习"], "duties": ["部署"]},
        )

        self.assertEqual(first, reordered)
        self.assertNotEqual(first, changed)
        self.assertTrue(first.startswith("job-version-"))


if __name__ == "__main__":
    unittest.main()
