import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.fetch_jobs import JobFilter, normalize_update_time
from scripts.import_offer_export import build_phase_pool, detect_phase
from scripts.state import FetcherState


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

    def test_embodied_role_scores_above_generic_role(self):
        config = {
            "filters": {
                "cities": ["深圳"],
                "industries": ["机器人", "互联网"],
                "graduation_year": "2027",
                "matching": {
                    "primary_keywords": ["具身智能", "VLA", "世界动作模型", "机器人学习"],
                    "secondary_keywords": ["ROS2", "推理优化", "嵌入式"],
                    "deprioritize_keywords": ["销售"],
                },
            }
        }
        job_filter = JobFilter(config, phase="提前批")
        embodied = {
            "企业名称": "机器人公司",
            "职位": "具身智能 VLA 机器人学习算法工程师",
            "工作地点": "深圳",
            "行业": "机器人",
            "学历要求": "硕士",
            "毕业年份": "2027",
            "招聘批次": "27届秋招提前批",
            "岗位描述": "负责世界动作模型、ROS2 真机部署和推理优化",
        }
        generic = {
            "企业名称": "互联网公司",
            "职位": "销售运营",
            "工作地点": "深圳",
            "行业": "互联网",
            "学历要求": "硕士",
            "毕业年份": "2027",
            "招聘批次": "27届秋招提前批",
        }

        self.assertGreater(job_filter.score(embodied), job_filter.score(generic))
        self.assertEqual(embodied["_target_track"], "具身智能")

    def test_seen_record_version_changes_with_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state = FetcherState(Path(temp_dir) / "state.json")
            original = {"企业名称": "机器人甲", "职位": "VLA算法", "更新时间": "2026-08-13"}
            state.remember_records([original])
            self.assertTrue(state.is_seen_record(original))
            changed = dict(original, 职位="VLA真机部署算法")
            self.assertFalse(state.is_seen_record(changed))

    def test_update_time_normalizes_platform_date_separator(self):
        self.assertEqual(normalize_update_time("2026/08/13"), "2026-08-13")
        self.assertEqual(normalize_update_time("2026-08-13"), "2026-08-13")


if __name__ == "__main__":
    unittest.main()
