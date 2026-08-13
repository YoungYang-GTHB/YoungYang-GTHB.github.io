import argparse
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.jobctl import cmd_shortlist


class ShortlistTests(unittest.TestCase):
    def test_default_zero_limit_outputs_all_qualified_jobs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs = Path(temp_dir) / "jobs.jsonl"
            records = [
                {"企业名称": f"公司{i}", "职位": "具身算法", "_match_score": score}
                for i, score in enumerate((90, 80, 70, 60, 30), start=1)
            ]
            jobs.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in records),
                encoding="utf-8",
            )
            output = StringIO()
            with redirect_stdout(output):
                result = cmd_shortlist(
                    argparse.Namespace(
                        phase="提前批",
                        input=str(jobs),
                        limit=0,
                        min_score=35,
                        json=False,
                        ledger="unused.yaml",
                    )
                )
            self.assertEqual(result, 0)
            self.assertIn("分数≥35 的 4 条；显示 4 条", output.getvalue())


if __name__ == "__main__":
    unittest.main()
