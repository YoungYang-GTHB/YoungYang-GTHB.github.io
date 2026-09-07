import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_artifact import (
    assert_valid_artifact,
    calculate_task_input_digest,
    validate_artifact,
    validate_task,
    validate_task_input_files,
)


def make_task(task_id: str = "research-example") -> dict:
    task = {
        "schema_version": 1,
        "run_id": "run-20260907-001",
        "run_epoch": 1,
        "task_id": task_id,
        "role": "research",
        "idempotency_key": f"research:{task_id}:20260907",
        "input_digest": "",
        "input_refs": [],
        "payload": {"official_entries": ["https://jobs.example/campus"]},
    }
    task["input_digest"] = calculate_task_input_digest(task)
    return task


def make_artifact(task: dict) -> dict:
    return {
        "schema_version": 1,
        "run_id": task["run_id"],
        "run_epoch": task["run_epoch"],
        "task_id": task["task_id"],
        "role": task["role"],
        "idempotency_key": task["idempotency_key"],
        "input_digest": task["input_digest"],
        "generated_at": "2026-09-07T10:00:00+08:00",
        "status": "succeeded",
        "facts": {
            "pool_scan": {
                "official_entry": "https://jobs.example/campus",
                "scanned_at": "2026-09-07T10:00:00+08:00",
                "total_jobs": 1,
                "pages_or_query_scope": "all pages",
                "complete": True,
                "graduation_year_verified": True,
                "full_time_verified": True,
            },
            "jobs": [{"job_id": "J1", "title": "具身算法工程师"}],
        },
        "evidence": [
            {
                "field": "job_pool",
                "url": "https://jobs.example/campus",
                "source_type": "official",
                "observed_at": "2026-09-07T10:00:00+08:00",
                "summary": "官方岗位池共一个岗位",
            }
        ],
        "blockers": [],
        "warnings": [],
        "next_action": "ranking",
    }


class ValidateArtifactTests(unittest.TestCase):
    def test_valid_research_artifact_matches_task(self):
        task = make_task()
        artifact = make_artifact(task)

        self.assertEqual(validate_task(task), [])
        self.assertEqual(validate_artifact(artifact), [])
        assert_valid_artifact(artifact, task)

    def test_research_success_requires_official_evidence(self):
        artifact = make_artifact(make_task())
        artifact["evidence"][0]["source_type"] = "third_party"

        errors = validate_artifact(artifact)

        self.assertTrue(any("官方证据" in error for error in errors))

    def test_research_success_rejects_empty_pool_scan(self):
        artifact = make_artifact(make_task())
        artifact["facts"]["pool_scan"] = {}
        artifact["facts"]["jobs"] = []

        errors = validate_artifact(artifact)

        self.assertTrue(any("pool_scan" in error for error in errors))

    def test_research_success_requires_verified_scope_and_eligibility(self):
        artifact = make_artifact(make_task())
        artifact["facts"]["pool_scan"].update(
            official_entry="",
            pages_or_query_scope="",
            graduation_year_verified=False,
            full_time_verified=False,
        )

        errors = validate_artifact(artifact)

        self.assertTrue(any("official_entry 不能为空" in error for error in errors))
        self.assertTrue(any("graduation_year_verified 必须为 true" in error for error in errors))
        self.assertTrue(any("full_time_verified 必须为 true" in error for error in errors))

    def test_research_pool_count_must_match_jobs(self):
        artifact = make_artifact(make_task())
        artifact["facts"]["pool_scan"]["total_jobs"] = 2

        errors = validate_artifact(artifact)

        self.assertTrue(any("total_jobs 必须与 jobs 数量一致" in error for error in errors))

    def test_form_success_rejects_empty_snapshot_fields(self):
        task = make_task("form-example")
        task["role"] = "form_prep"
        task["idempotency_key"] = "form:example:20260907"
        task["input_digest"] = calculate_task_input_digest(task)
        artifact = make_artifact(task)
        artifact["role"] = "form_prep"
        artifact["idempotency_key"] = task["idempotency_key"]
        artifact["input_digest"] = task["input_digest"]
        artifact["facts"] = {
            "form_snapshot": {
                "company_key": "example",
                "job_id": "",
                "title": "",
                "page_url": "",
                "filled_fields": [],
                "validation_errors": [],
            },
            "missing_fields": [],
            "resume": {"filename": "resume.pdf", "sha256": "a" * 64},
        }
        artifact["evidence"] = []

        errors = validate_artifact(artifact)

        self.assertTrue(any("form_snapshot.job_id 不能为空" in error for error in errors))
        self.assertTrue(any("form_snapshot.page_url 不能为空" in error for error in errors))

        artifact["facts"]["form_snapshot"].update(
            job_id="J-42", title="具身算法工程师", page_url="https://jobs.example/J-42"
        )
        artifact["facts"]["resume"]["filename"] = ""
        self.assertTrue(
            any("resume.filename 不能为空" in error for error in validate_artifact(artifact))
        )

    def test_artifact_rejects_sensitive_url_parameters(self):
        artifact = make_artifact(make_task())
        artifact["evidence"][0]["url"] = "https://jobs.example/form?access_token=secret"

        errors = validate_artifact(artifact)

        self.assertTrue(any("敏感查询参数" in error for error in errors))

    def test_task_rejects_sensitive_payload_fields(self):
        task = make_task()
        task["payload"]["password"] = "do-not-store"

        errors = validate_task(task)

        self.assertTrue(any("敏感字段" in error for error in errors))

    def test_artifact_rejects_identity_and_phone_values_under_generic_keys(self):
        artifact = make_artifact(make_task())
        artifact["warnings"] = ["发现11010519491231002X和13912345678"]

        errors = validate_artifact(artifact)

        self.assertTrue(any("身份证号" in error for error in errors))
        self.assertTrue(any("手机号" in error for error in errors))

    def test_artifact_must_match_task_identity(self):
        task = make_task()
        artifact = make_artifact(task)
        artifact["input_digest"] = "b" * 64

        with self.assertRaisesRegex(ValueError, "与任务不一致"):
            assert_valid_artifact(artifact, task)

    def test_task_rejects_stale_input_digest(self):
        task = make_task()
        task["payload"]["official_entries"] = ["https://jobs.example/changed"]

        self.assertTrue(any("input_digest" in error for error in validate_task(task)))

    def test_declared_input_file_hash_is_verified(self):
        import hashlib
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "official.json"
            source.write_text("original", encoding="utf-8")
            task = make_task()
            task["input_refs"] = [
                {"path": "official.json", "sha256": hashlib.sha256(b"original").hexdigest()}
            ]
            task["input_digest"] = calculate_task_input_digest(task)
            self.assertEqual(validate_task_input_files(task, base_dir=root), [])
            source.write_text("changed", encoding="utf-8")
            self.assertTrue(validate_task_input_files(task, base_dir=root))

    def test_artifact_epoch_must_match_current_task_epoch(self):
        task = make_task()
        artifact = make_artifact(task)
        artifact["run_epoch"] = 2

        with self.assertRaisesRegex(ValueError, "run_epoch 与任务不一致"):
            assert_valid_artifact(artifact, task)

    def test_role_specific_fields_are_required(self):
        task = make_task("audit-example")
        task.update(
            role="audit",
            idempotency_key="audit:audit-example:20260907",
        )
        artifact = make_artifact(task)
        artifact["facts"] = {"checks": []}
        artifact["evidence"] = []

        errors = validate_artifact(artifact)

        self.assertTrue(any("facts.decision" in error for error in errors))

    def test_role_specific_fields_have_stable_types(self):
        artifact = make_artifact(make_task())
        artifact["facts"]["jobs"] = {"J1": "not-an-array"}

        errors = validate_artifact(artifact)

        self.assertTrue(any("facts.jobs 必须是 list" in error for error in errors))

    def test_ranking_contract_has_fixed_gates_scores_and_no_failed_recommendation(self):
        task = make_task("ranking-example")
        task.update(role="ranking", idempotency_key="ranking:example:20260907")
        task["input_digest"] = calculate_task_input_digest(task)
        artifact = make_artifact(task)
        artifact["facts"] = {
            "ranking": [
                {
                    "rank": 1,
                    "job_key": "job-1",
                    "hard_gate": "fail",
                    "overall_score": 90,
                    "scores": {
                        "experience_fit": 90,
                        "deployment_fit": 90,
                        "research_fit": 90,
                        "location_fit": 90,
                        "quota_risk": 0,
                        "phase_risk": 0,
                        "evidence_quality": 90,
                    },
                    "matching_evidence": [],
                    "capability_gaps": ["学历不满足"],
                    "exclusion_reason": "硬门槛失败",
                }
            ],
            "recommendation": {"job_key": "job-1", "reason": "错误推荐"},
        }
        artifact["evidence"] = []

        errors = validate_artifact(artifact)

        self.assertTrue(any("硬门槛失败岗位" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
