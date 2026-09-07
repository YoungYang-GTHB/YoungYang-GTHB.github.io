#!/usr/bin/env python3
"""SQLite-backed runtime queue for job-hunter read-only worker tasks.

The queue never edits recruiting ledgers or submits applications.  Workers
produce immutable JSON artifacts; the coordinator remains the only canonical
ledger writer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from browser_lease import BrowserLease, BrowserLeaseError, DEFAULT_STATE_DIR
from validate_artifact import (
    ValidationError,
    assert_valid_artifact,
    load_json_object,
    validate_task_input_files,
    validate_task,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = (
    PROJECT_ROOT
    / "career"
    / "求职投递"
    / "2027届"
    / ".runtime"
    / "job-hunter.sqlite3"
)
ROLES = ("discovery", "research", "ranking", "form_prep", "audit")


class QueueError(RuntimeError):
    """Raised when a queue transition is unsafe or invalid."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_task_digest(task: dict[str, Any]) -> str:
    stable = {key: value for key, value in task.items() if key != "created_at"}
    return hashlib.sha256(canonical_json(stable).encode("utf-8")).hexdigest()


def normalized_task(document: dict[str, Any]) -> dict[str, Any]:
    task = dict(document)
    task.setdefault("company_key", "")
    task.setdefault("phase", "")
    task.setdefault("priority", 100)
    task.setdefault("max_attempts", 3)
    task.setdefault("created_at", iso_time())
    task.setdefault("input_refs", [])
    errors = validate_task(task)
    if errors:
        raise QueueError("任务校验失败:\n- " + "\n- ".join(errors))
    return task


class JobQueue:
    def __init__(
        self,
        path: str | Path = DEFAULT_DB,
        *,
        browser_state_dir: str | Path = DEFAULT_STATE_DIR,
    ):
        self.path = Path(path)
        self.browser_state_dir = Path(browser_state_dir)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.parent.is_symlink() or not self.path.parent.is_dir():
            raise QueueError(f"runtime directory is unsafe: {self.path.parent}")
        os.chmod(self.path.parent, 0o700)
        if self.path.exists() and (self.path.is_symlink() or not self.path.is_file()):
            raise QueueError(f"runtime database is unsafe: {self.path}")
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                run_epoch INTEGER NOT NULL,
                role TEXT NOT NULL,
                company_key TEXT NOT NULL DEFAULT '',
                phase TEXT NOT NULL DEFAULT '',
                idempotency_key TEXT NOT NULL UNIQUE,
                input_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                attempt INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                not_before TEXT NOT NULL,
                lease_owner TEXT,
                lease_expires_at TEXT,
                artifact_path TEXT,
                artifact_sha256 TEXT,
                consumed_by TEXT,
                consumed_at TEXT,
                error_code TEXT,
                error_message TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS tasks_claim_idx "
            "ON tasks(status, role, priority, not_before, created_at)"
        )
        # Additive migration for queues created by an earlier MVP revision.
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)")}
        if "consumed_by" not in columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN consumed_by TEXT")
        if "consumed_at" not in columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN consumed_at TEXT")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return connection

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        result["task"] = json.loads(result.pop("payload_json"))
        return result

    def dispatch(self, document: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        task = normalized_task(document)
        payload_sha = semantic_task_digest(task)
        now = iso_time()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM tasks WHERE idempotency_key = ?",
                (task["idempotency_key"],),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_sha:
                    connection.rollback()
                    raise QueueError(
                        "相同 idempotency_key 对应不同任务内容；请修正键或输入"
                    )
                connection.commit()
                return self._row(existing) or {}, True
            collision = connection.execute(
                "SELECT idempotency_key FROM tasks WHERE task_id = ?", (task["task_id"],)
            ).fetchone()
            if collision is not None:
                connection.rollback()
                raise QueueError(f"task_id 已被其他幂等任务使用: {task['task_id']}")
            connection.execute(
                """
                INSERT INTO tasks (
                    task_id, run_id, run_epoch, role, company_key, phase,
                    idempotency_key, input_digest, payload_json, payload_sha256,
                    priority, status, attempt, max_attempts, created_at,
                    updated_at, not_before
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?)
                """,
                (
                    task["task_id"],
                    task["run_id"],
                    task["run_epoch"],
                    task["role"],
                    task["company_key"],
                    task["phase"],
                    task["idempotency_key"],
                    task["input_digest"],
                    canonical_json(task),
                    payload_sha,
                    task["priority"],
                    task["max_attempts"],
                    task["created_at"],
                    now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task["task_id"],)
            ).fetchone()
            connection.commit()
            return self._row(row) or {}, False

    @staticmethod
    def _recover_expired(connection: sqlite3.Connection, now: str) -> None:
        connection.execute(
            """
            UPDATE tasks
            SET status = CASE WHEN attempt >= max_attempts THEN 'failed' ELSE 'pending' END,
                error_code = 'lease_expired',
                error_message = 'worker lease expired before completion',
                lease_owner = NULL,
                lease_expires_at = NULL,
                not_before = ?,
                updated_at = ?
            WHERE status = 'leased' AND lease_expires_at <= ?
            """,
            (now, now, now),
        )

    def claim(
        self,
        *,
        worker: str,
        role: str = "",
        run_id: str = "",
        lease_seconds: int = 300,
    ) -> dict[str, Any] | None:
        if not worker.strip():
            raise QueueError("worker 不能为空")
        if role and role not in ROLES:
            raise QueueError(f"未知 worker role: {role}")
        if lease_seconds < 30 or lease_seconds > 3600:
            raise QueueError("lease-seconds 必须在 30-3600 之间")
        now_dt = utc_now()
        now = iso_time(now_dt)
        expires = iso_time(now_dt + timedelta(seconds=lease_seconds))
        clauses = ["status = 'pending'", "not_before <= ?"]
        values: list[Any] = [now]
        if role:
            clauses.append("role = ?")
            values.append(role)
        if run_id:
            clauses.append("run_id = ?")
            values.append(run_id)
        where = " AND ".join(clauses)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._recover_expired(connection, now)
            candidate = connection.execute(
                f"SELECT task_id FROM tasks WHERE {where} "
                "ORDER BY priority ASC, created_at ASC, task_id ASC LIMIT 1",
                values,
            ).fetchone()
            if candidate is None:
                connection.commit()
                return None
            connection.execute(
                """
                UPDATE tasks
                SET status = 'leased', attempt = attempt + 1, lease_owner = ?,
                    lease_expires_at = ?, updated_at = ?, error_code = NULL,
                    error_message = NULL
                WHERE task_id = ? AND status = 'pending'
                """,
                (worker, expires, now, candidate["task_id"]),
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (candidate["task_id"],)
            ).fetchone()
            connection.commit()
            return self._row(row)

    def heartbeat(self, task_id: str, worker: str, lease_seconds: int = 300) -> dict[str, Any]:
        if lease_seconds < 30 or lease_seconds > 3600:
            raise QueueError("lease-seconds 必须在 30-3600 之间")
        now_dt = utc_now()
        now = iso_time(now_dt)
        expires = iso_time(now_dt + timedelta(seconds=lease_seconds))
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            self._assert_lease(row, task_id, worker, now)
            connection.execute(
                "UPDATE tasks SET lease_expires_at = ?, updated_at = ? WHERE task_id = ?",
                (expires, now, task_id),
            )
            updated = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            connection.commit()
            return self._row(updated) or {}

    @staticmethod
    def _assert_lease(
        row: sqlite3.Row | None, task_id: str, worker: str, now: str
    ) -> None:
        if row is None:
            raise QueueError(f"任务不存在: {task_id}")
        if row["status"] != "leased":
            raise QueueError(f"任务状态不是 leased: {row['status']}")
        if row["lease_owner"] != worker:
            raise QueueError(f"任务租约属于其他 worker: {row['lease_owner']}")
        if row["lease_expires_at"] <= now:
            raise QueueError("任务租约已经过期；请重新 claim")

    def complete(
        self,
        task_id: str,
        worker: str,
        artifact_path: str | Path,
        *,
        browser_lease_id: str = "",
    ) -> dict[str, Any]:
        artifact_file = Path(artifact_path)
        artifact = load_json_object(artifact_file)
        artifact_bytes = artifact_file.read_bytes()
        artifact_sha = hashlib.sha256(artifact_bytes).hexdigest()
        now = iso_time()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            self._assert_lease(row, task_id, worker, now)
            task = json.loads(row["payload_json"])
            if task["role"] == "form_prep":
                expected_target = str(task.get("payload", {}).get("browser_target_id") or "").strip()
                if not expected_target:
                    connection.rollback()
                    raise QueueError("form_prep 任务缺少 browser_target_id")
                try:
                    browser_owner = BrowserLease(self.browser_state_dir).assert_owned(
                        browser_lease_id
                    )
                except BrowserLeaseError as error:
                    connection.rollback()
                    raise QueueError(f"form_prep 浏览器租约无效: {error}") from error
                if browser_owner.get("agent") != worker:
                    connection.rollback()
                    raise QueueError("form_prep 浏览器租约不属于当前 worker")
                if browser_owner.get("task_id") != task_id:
                    connection.rollback()
                    raise QueueError("form_prep 浏览器租约未绑定当前 task_id")
                if browser_owner.get("target_id") != expected_target:
                    connection.rollback()
                    raise QueueError("form_prep 浏览器租约未绑定指定 target_id")
            try:
                assert_valid_artifact(artifact, task)
            except ValidationError as error:
                connection.rollback()
                raise QueueError(str(error)) from error
            if artifact["status"] != "succeeded":
                connection.rollback()
                raise QueueError("complete 只接受 status=succeeded 的产物；阻断或失败请用 fail")
            connection.execute(
                """
                UPDATE tasks SET status = 'succeeded', artifact_path = ?,
                    artifact_sha256 = ?, lease_owner = NULL, lease_expires_at = NULL,
                    updated_at = ?, error_code = NULL, error_message = NULL
                WHERE task_id = ?
                """,
                (str(artifact_file.resolve()), artifact_sha, now, task_id),
            )
            updated = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            connection.commit()
            return self._row(updated) or {}

    def fail(
        self,
        task_id: str,
        worker: str,
        *,
        error_code: str,
        message: str,
        retry_delay: int = 0,
        terminal: bool = False,
        blocked: bool = False,
        artifact_path: str | Path | None = None,
    ) -> dict[str, Any]:
        if retry_delay < 0 or retry_delay > 86400:
            raise QueueError("retry-delay 必须在 0-86400 之间")
        if terminal and blocked:
            raise QueueError("--terminal 与 --blocked 不能同时使用")
        now_dt = utc_now()
        now = iso_time(now_dt)
        artifact: dict[str, Any] | None = None
        artifact_file: Path | None = None
        artifact_sha = ""
        if artifact_path:
            artifact_file = Path(artifact_path)
            artifact = load_json_object(artifact_file)
            artifact_sha = hashlib.sha256(artifact_file.read_bytes()).hexdigest()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            self._assert_lease(row, task_id, worker, now)
            if artifact is not None:
                task = json.loads(row["payload_json"])
                try:
                    assert_valid_artifact(artifact, task)
                except ValidationError as error:
                    connection.rollback()
                    raise QueueError(str(error)) from error
                expected_status = "blocked" if blocked else "failed"
                if artifact["status"] != expected_status:
                    connection.rollback()
                    raise QueueError(
                        f"fail 产物状态必须为 {expected_status}，当前为 {artifact['status']}"
                    )
            if blocked:
                status = "blocked"
            elif terminal or row["attempt"] >= row["max_attempts"]:
                status = "failed"
            else:
                status = "pending"
            not_before = iso_time(now_dt + timedelta(seconds=retry_delay))
            connection.execute(
                """
                UPDATE tasks SET status = ?, not_before = ?, lease_owner = NULL,
                    lease_expires_at = NULL, updated_at = ?, error_code = ?,
                    error_message = ?, artifact_path = ?, artifact_sha256 = ?
                WHERE task_id = ?
                """,
                (
                    status,
                    not_before,
                    now,
                    error_code,
                    message,
                    str(artifact_file.resolve()) if artifact_file else None,
                    artifact_sha or None,
                    task_id,
                ),
            )
            updated = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            connection.commit()
            return self._row(updated) or {}

    def consume(
        self,
        task_id: str,
        *,
        coordinator: str,
        artifact_sha256: str = "",
    ) -> dict[str, Any]:
        """Mark one validated artifact as merged by the single writer."""
        coordinator = str(coordinator or "").strip()
        if not coordinator:
            raise QueueError("coordinator 不能为空")
        now = iso_time()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                connection.rollback()
                raise QueueError(f"任务不存在: {task_id}")
            if row["status"] == "consumed":
                if row["consumed_by"] != coordinator:
                    connection.rollback()
                    raise QueueError(f"任务已由其他 coordinator 消费: {row['consumed_by']}")
                connection.commit()
                return self._row(row) or {}
            if row["status"] != "succeeded":
                connection.rollback()
                raise QueueError(f"只有 succeeded 任务可以消费，当前为: {row['status']}")
            if artifact_sha256 and row["artifact_sha256"] != artifact_sha256:
                connection.rollback()
                raise QueueError("artifact SHA-256 与队列记录不一致")
            connection.execute(
                "UPDATE tasks SET status = 'consumed', consumed_by = ?, "
                "consumed_at = ?, updated_at = ? WHERE task_id = ?",
                (coordinator, now, now, task_id),
            )
            updated = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            connection.commit()
            return self._row(updated) or {}

    def status(
        self, *, run_id: str = "", task_id: str = "", limit: int = 50
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if run_id:
            clauses.append("run_id = ?")
            values.append(run_id)
        if task_id:
            clauses.append("task_id = ?")
            values.append(task_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.append(limit)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM tasks {where} "
                "ORDER BY created_at DESC, task_id ASC LIMIT ?",
                values,
            ).fetchall()
        return [self._row(row) or {} for row in rows]


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="runtime SQLite path")
    parser.add_argument(
        "--browser-state-dir",
        default=str(DEFAULT_STATE_DIR),
        help="共享浏览器租约目录",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dispatch = subparsers.add_parser("dispatch", help="幂等加入一个 task JSON")
    dispatch.add_argument("task", help="符合 schemas/task.schema.json 的文件")

    claim = subparsers.add_parser("claim", help="领取一个可执行任务")
    claim.add_argument("--worker", required=True)
    claim.add_argument("--role", choices=("", *ROLES), default="")
    claim.add_argument("--run-id", default="")
    claim.add_argument("--lease-seconds", type=int, default=300)

    heartbeat = subparsers.add_parser("heartbeat", help="续期当前 worker 的租约")
    heartbeat.add_argument("task_id")
    heartbeat.add_argument("--worker", required=True)
    heartbeat.add_argument("--lease-seconds", type=int, default=300)

    complete = subparsers.add_parser("complete", help="校验并登记成功产物")
    complete.add_argument("task_id")
    complete.add_argument("--worker", required=True)
    complete.add_argument("--artifact", required=True)
    complete.add_argument(
        "--browser-lease-id",
        default="",
        help="form_prep 完成时必须提供的当前浏览器租约 ID",
    )

    consume = subparsers.add_parser("consume", help="由 Coordinator 标记已合并产物")
    consume.add_argument("task_id")
    consume.add_argument("--coordinator", required=True)
    consume.add_argument("--artifact-sha256", default="")

    fail = subparsers.add_parser("fail", help="记录失败、阻断或安排重试")
    fail.add_argument("task_id")
    fail.add_argument("--worker", required=True)
    fail.add_argument("--error-code", required=True)
    fail.add_argument("--message", required=True)
    fail.add_argument("--artifact", default="", help="可选 blocked/failed artifact JSON")
    fail.add_argument("--retry-delay", type=int, default=0)
    mode = fail.add_mutually_exclusive_group()
    mode.add_argument("--terminal", action="store_true")
    mode.add_argument("--blocked", action="store_true")

    status = subparsers.add_parser("status", help="查看队列状态")
    status.add_argument("--run-id", default="")
    status.add_argument("--task-id", default="")
    status.add_argument("--limit", type=int, default=50)
    status.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    queue = JobQueue(args.db, browser_state_dir=args.browser_state_dir)
    try:
        if args.command == "dispatch":
            task = load_json_object(args.task)
            input_errors = validate_task_input_files(task, base_dir=Path(args.task).parent)
            if input_errors:
                raise QueueError("任务输入文件校验失败:\n- " + "\n- ".join(input_errors))
            row, reused = queue.dispatch(task)
            print_json({"reused": reused, "task": row})
        elif args.command == "claim":
            row = queue.claim(
                worker=args.worker,
                role=args.role,
                run_id=args.run_id,
                lease_seconds=args.lease_seconds,
            )
            print_json(row)
        elif args.command == "heartbeat":
            print_json(queue.heartbeat(args.task_id, args.worker, args.lease_seconds))
        elif args.command == "complete":
            print_json(
                queue.complete(
                    args.task_id,
                    args.worker,
                    args.artifact,
                    browser_lease_id=args.browser_lease_id,
                )
            )
        elif args.command == "consume":
            print_json(
                queue.consume(
                    args.task_id,
                    coordinator=args.coordinator,
                    artifact_sha256=args.artifact_sha256,
                )
            )
        elif args.command == "fail":
            print_json(
                queue.fail(
                    args.task_id,
                    args.worker,
                    error_code=args.error_code,
                    message=args.message,
                    retry_delay=args.retry_delay,
                    terminal=args.terminal,
                    blocked=args.blocked,
                    artifact_path=args.artifact or None,
                )
            )
        elif args.command == "status":
            rows = queue.status(run_id=args.run_id, task_id=args.task_id, limit=args.limit)
            if args.json:
                print_json(rows)
            else:
                print("status\tattempt\trole\trun_id\ttask_id\tlease_owner\terror")
                for row in rows:
                    print(
                        f"{row['status']}\t{row['attempt']}/{row['max_attempts']}\t"
                        f"{row['role']}\t{row['run_id']}\t{row['task_id']}\t"
                        f"{row.get('lease_owner') or '—'}\t{row.get('error_code') or '—'}"
                    )
        else:  # pragma: no cover
            parser.error(f"unknown command: {args.command}")
    except (QueueError, ValidationError, OSError, sqlite3.Error) as error:
        print(f"[jobqueue] {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
