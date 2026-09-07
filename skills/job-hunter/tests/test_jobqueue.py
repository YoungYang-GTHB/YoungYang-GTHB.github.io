import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from jobqueue import JobQueue, QueueError
from browser_lease import BrowserLease
from validate_artifact import calculate_task_input_digest


def make_task(task_id: str = "research-example") -> dict:
    task = {
        "schema_version": 1,
        "run_id": "run-20260907-001",
        "run_epoch": 1,
        "task_id": task_id,
        "role": "research",
        "idempotency_key": f"research:{task_id}:20260907",
        "input_digest": "",
        "company_key": "example",
        "phase": "秋招",
        "priority": 10,
        "max_attempts": 2,
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


def make_form_task(task_id: str = "form-example", target_id: str = "TARGET-42") -> dict:
    task = {
        "schema_version": 1,
        "run_id": "run-20260907-forms",
        "run_epoch": 1,
        "task_id": task_id,
        "role": "form_prep",
        "idempotency_key": f"form:{task_id}:20260907",
        "input_digest": "",
        "company_key": "example",
        "phase": "秋招",
        "priority": 5,
        "max_attempts": 2,
        "input_refs": [],
        "payload": {
            "browser_target_id": target_id,
            "allowed_field_names": ["姓名", "学校"],
        },
    }
    task["input_digest"] = calculate_task_input_digest(task)
    return task


def make_form_artifact(task: dict) -> dict:
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
            "form_snapshot": {
                "company_key": "example",
                "job_id": "J-42",
                "title": "机器人软件工程师",
                "page_url": "https://jobs.example/application/J-42",
                "filled_fields": ["姓名", "学校"],
                "validation_errors": [],
            },
            "missing_fields": [],
            "resume": {"filename": "resume-vla-zh.pdf", "sha256": "a" * 64},
        },
        "evidence": [],
        "blockers": [],
        "warnings": [],
        "next_action": "audit",
    }


class JobQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "queue.sqlite3"
        self.queue = JobQueue(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_is_idempotent_and_rejects_key_reuse(self):
        task = make_task()
        first, reused_first = self.queue.dispatch(task)
        second, reused_second = self.queue.dispatch(task)

        self.assertFalse(reused_first)
        self.assertTrue(reused_second)
        self.assertEqual(first["task_id"], second["task_id"])

        changed = make_task()
        changed["payload"] = {"official_entries": ["https://jobs.example/other"]}
        changed["input_digest"] = calculate_task_input_digest(changed)
        with self.assertRaisesRegex(QueueError, "相同 idempotency_key"):
            self.queue.dispatch(changed)

    def test_runtime_directory_and_database_are_private(self):
        self.queue.dispatch(make_task())
        self.assertEqual(self.db.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.db.stat().st_mode & 0o777, 0o600)

    def test_symlink_database_is_rejected(self):
        target = Path(self.temp_dir.name) / "real.sqlite3"
        target.touch()
        linked = Path(self.temp_dir.name) / "linked.sqlite3"
        os.symlink(target, linked)
        with self.assertRaisesRegex(QueueError, "database is unsafe"):
            JobQueue(linked).dispatch(make_task())

    def test_concurrent_claim_leases_task_only_once(self):
        self.queue.dispatch(make_task())
        barrier = threading.Barrier(2)
        claimed: list[dict | None] = []

        def worker(name: str) -> None:
            barrier.wait()
            claimed.append(JobQueue(self.db).claim(worker=name, role="research"))

        threads = [threading.Thread(target=worker, args=(f"worker-{index}",)) for index in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(item is not None for item in claimed), 1)
        leased = next(item for item in claimed if item is not None)
        self.assertEqual(leased["status"], "leased")
        self.assertEqual(leased["attempt"], 1)

    def test_heartbeat_and_retry_until_max_attempts(self):
        self.queue.dispatch(make_task())
        claimed = self.queue.claim(worker="worker-a", lease_seconds=30)
        self.assertIsNotNone(claimed)
        before = claimed["lease_expires_at"]

        heartbeat = self.queue.heartbeat("research-example", "worker-a", 300)
        self.assertGreater(heartbeat["lease_expires_at"], before)

        retry = self.queue.fail(
            "research-example",
            "worker-a",
            error_code="http_503",
            message="retry",
        )
        self.assertEqual(retry["status"], "pending")

        claimed_again = self.queue.claim(worker="worker-b")
        self.assertEqual(claimed_again["attempt"], 2)
        exhausted = self.queue.fail(
            "research-example",
            "worker-b",
            error_code="http_503",
            message="exhausted",
        )
        self.assertEqual(exhausted["status"], "failed")

    def test_expired_lease_is_recovered_on_next_claim(self):
        self.queue.dispatch(make_task())
        self.queue.claim(worker="worker-a")
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "UPDATE tasks SET lease_expires_at = '2000-01-01T00:00:00Z' "
                "WHERE task_id = 'research-example'"
            )

        reclaimed = self.queue.claim(worker="worker-b")
        self.assertIsNotNone(reclaimed)
        self.assertEqual(reclaimed["lease_owner"], "worker-b")
        self.assertEqual(reclaimed["attempt"], 2)

    def test_complete_validates_and_hashes_artifact(self):
        task = make_task()
        self.queue.dispatch(task)
        self.queue.claim(worker="worker-a")
        artifact_path = Path(self.temp_dir.name) / "artifact.json"
        artifact_path.write_text(
            json.dumps(make_artifact(task), ensure_ascii=False), encoding="utf-8"
        )

        completed = self.queue.complete("research-example", "worker-a", artifact_path)

        self.assertEqual(completed["status"], "succeeded")
        self.assertEqual(len(completed["artifact_sha256"]), 64)
        self.assertEqual(completed["artifact_path"], str(artifact_path.resolve()))
        with self.assertRaisesRegex(QueueError, "状态不是 leased"):
            self.queue.complete("research-example", "worker-a", artifact_path)

        consumed = self.queue.consume(
            "research-example",
            coordinator="root",
            artifact_sha256=completed["artifact_sha256"],
        )
        self.assertEqual(consumed["status"], "consumed")
        self.assertEqual(consumed["consumed_by"], "root")
        self.assertEqual(
            self.queue.consume("research-example", coordinator="root")["status"],
            "consumed",
        )

    def test_form_complete_requires_matching_live_browser_lease(self):
        browser_state = Path(self.temp_dir.name) / "browser-state"
        queue = JobQueue(self.db, browser_state_dir=browser_state)
        task = make_form_task()
        queue.dispatch(task)
        queue.claim(worker="form-worker")
        artifact_path = Path(self.temp_dir.name) / "form-artifact.json"
        artifact_path.write_text(
            json.dumps(make_form_artifact(task), ensure_ascii=False), encoding="utf-8"
        )

        with self.assertRaisesRegex(QueueError, "浏览器租约无效"):
            queue.complete(task["task_id"], "form-worker", artifact_path)

        owner = BrowserLease(browser_state).acquire(
            agent="form-worker",
            task_id=task["task_id"],
            company="example",
            target_id=task["payload"]["browser_target_id"],
            origin="https://jobs.example/application/J-42?token=redacted",
        )
        completed = queue.complete(
            task["task_id"],
            "form-worker",
            artifact_path,
            browser_lease_id=owner["lease_id"],
        )

        self.assertEqual(completed["status"], "succeeded")
        self.assertNotIn(owner["lease_id"], json.dumps(completed, ensure_ascii=False))

    def test_consume_rejects_unfinished_or_mismatched_artifact(self):
        self.queue.dispatch(make_task())
        with self.assertRaisesRegex(QueueError, "只有 succeeded"):
            self.queue.consume("research-example", coordinator="root")

    def test_fail_can_record_a_valid_blocked_artifact(self):
        task = make_task()
        self.queue.dispatch(task)
        self.queue.claim(worker="worker-a")
        artifact = make_artifact(task)
        artifact.update(status="blocked", facts={}, evidence=[])
        artifact_path = Path(self.temp_dir.name) / "blocked.json"
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")

        blocked = self.queue.fail(
            "research-example",
            "worker-a",
            error_code="login_required",
            message="等待本人登录",
            blocked=True,
            artifact_path=artifact_path,
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["artifact_path"], str(artifact_path.resolve()))
        self.assertEqual(len(blocked["artifact_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
