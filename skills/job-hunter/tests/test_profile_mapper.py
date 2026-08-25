import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.profile_mapper import build_profile, normalize_date, split_period


class ProfileMapperTests(unittest.TestCase):
    def test_date_normalization_preserves_full_birthday(self):
        self.assertEqual(normalize_date("2024 年 3 月 20 日"), "2024-03-20")
        self.assertEqual(split_period("2026.04 - 至今"), ("2026-04", "", "是"))

    def test_profile_uses_confirmed_capability_boundaries(self):
        profile = build_profile(compact=True)

        self.assertEqual(profile["personal"]["birthDate"], "2002-03-20")
        self.assertNotIn("机械设计", profile["skills"]["domainKnowledge"])
        self.assertIn("算法训练与部署", profile["skills"]["domainKnowledge"])

    def test_part_time_technical_partner_is_not_dropped(self):
        profile = build_profile(compact=True)
        work = profile["workExperiences"]

        self.assertTrue(any(item["company"].startswith("中秦禾瑞") for item in work))
        partner = next(item for item in work if item["company"].startswith("中秦禾瑞"))
        self.assertEqual(partner["title"], "技术合伙人")
        self.assertEqual(partner["employmentType"], "兼职")


if __name__ == "__main__":
    unittest.main()
