import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.exclusions import ExclusionStore, normalize_url


class ExclusionStoreTests(unittest.TestCase):
    def test_non_url_contact_instruction_does_not_abort_matching(self):
        self.assertEqual(normalize_url("邮箱投递：zpc@wch.cn"), "")
        self.assertEqual(normalize_url("//邮箱投递：zpc@wch.cn"), "")

    def test_matches_company_and_position_in_same_phase(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ExclusionStore(Path(temp_dir) / "exclusions.yaml")
            store.add(
                {
                    "id": "example-hold",
                    "company": "卓驭科技",
                    "position_keyword": "多模态数据",
                    "phase": "提前批",
                    "reason": "本人暂不投递",
                }
            )
            job = {
                "企业名称": "卓驭科技有限公司",
                "职位": "多模态数据与评测算法岗",
            }
            self.assertIsNotNone(store.match(job, phase="提前批"))
            self.assertIsNone(store.match(job, phase="秋招"))

    def test_job_update_does_not_bypass_stable_job_id_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ExclusionStore(Path(temp_dir) / "exclusions.yaml")
            store.add(
                {
                    "id": "low-fit-id",
                    "job_id": "J13889",
                    "reason": "低匹配",
                }
            )
            self.assertIsNotNone(
                store.match({"岗位ID": "J13889", "职位": "更新后的标题"})
            )

    def test_disable_rule_allows_reevaluation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ExclusionStore(Path(temp_dir) / "exclusions.yaml")
            store.add({"id": "temporary", "company": "示例公司", "reason": "暂缓"})
            store.disable("temporary")
            self.assertIsNone(store.match({"企业名称": "示例公司"}))

    def test_job_id_rule_matches_even_when_company_field_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ExclusionStore(Path(temp_dir) / "exclusions.yaml")
            store.add(
                {
                    "id": "stable-id",
                    "company": "杰瑞集团",
                    "position_keyword": "RAG",
                    "job_id": "J13889",
                    "reason": "已决策排除",
                }
            )
            self.assertIsNotNone(store.match({"岗位ID": "J13889"}))


if __name__ == "__main__":
    unittest.main()
