import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.import_offer_export import build_phase_pool, detect_phase


class OfferExportImportTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "filters": {
                "cities": [],
                "exclude_cities": [],
                "industries": [],
                "exclude_industries": [],
                "education_keywords": [],
                "graduation_year": "2027",
            }
        }

    def test_phase_detection_prefers_advance_over_autumn(self):
        self.assertEqual(detect_phase({"招聘批次": "27届秋招提前批"}), "提前批")
        self.assertEqual(detect_phase({"招聘批次": "27届秋招"}), "秋招")
        self.assertEqual(detect_phase({"招聘批次": "27届春招"}), "春招")
        self.assertEqual(detect_phase({"招聘批次": "日常招聘"}), "未知")

    def test_phase_pool_excludes_other_phases_and_preserves_deadline(self):
        records = [
            {
                "企业名称": "机器人甲",
                "职位": "嵌入式工程师",
                "招聘批次": "27届秋招提前批",
                "毕业年份": "2027",
                "投递地址": "https://jobs.example/a",
                "截止时间": "2026-08-20",
            },
            {
                "企业名称": "机器人乙",
                "职位": "算法工程师",
                "招聘批次": "27届秋招",
                "毕业年份": "2027",
                "投递地址": "https://jobs.example/b",
            },
            {
                "企业名称": "机器人丙",
                "职位": "控制工程师",
                "招聘批次": "27届秋招提前批",
                "毕业年份": "2026",
                "投递地址": "https://jobs.example/c",
            },
        ]

        selected = build_phase_pool(records, "提前批", self.config)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["企业名称"], "机器人甲")
        self.assertEqual(selected[0]["截止时间"], "2026-08-20")
        self.assertEqual(selected[0]["_deadline_status"], "已记录")


if __name__ == "__main__":
    unittest.main()
