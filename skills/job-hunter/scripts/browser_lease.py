#!/usr/bin/env python3
"""Cooperative global lease for mutating the shared recruitment browser.

The browser is a single, logged-in Chrome profile.  Every cooperating agent
must acquire this lease before navigation, DOM mutation, file upload, target
focus/close, or submission.  ``flock`` serializes lease state transitions;
the expiring owner record provides crash recovery across processes.

This module deliberately does not connect to Chrome.  It is a small safety
primitive that CDP callers can import without gaining any additional browser
capability.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import secrets
import socket
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import urlsplit


DEFAULT_STATE_DIR = Path("/root/.local/state/youngyang-browser")
DEFAULT_TTL_SECONDS = 180
MIN_TTL_SECONDS = 10
MAX_TTL_SECONDS = 3600


class BrowserLeaseError(RuntimeError):
    """Raised when the shared browser lease cannot be acquired or updated."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _safe_origin(value: str) -> str:
    """Keep only an origin; never persist query strings or fragments."""

    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise BrowserLeaseError("origin 必须是有效的 http(s) 地址")
    return f"{parsed.scheme}://{parsed.netloc}"


class BrowserLease:
    """Manage an expiring lease protected by an inter-process file lock."""

    def __init__(
        self,
        state_dir: str | Path = DEFAULT_STATE_DIR,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.lock_path = self.state_dir / "browser.lock"
        self.owner_path = self.state_dir / "ownership.json"
        self._clock = clock or _utc_now

    def _now(self) -> datetime:
        return _as_utc(self._clock())

    def _ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_dir.is_symlink() or not self.state_dir.is_dir():
            raise BrowserLeaseError(f"浏览器运行态目录不安全: {self.state_dir}")
        os.chmod(self.state_dir, 0o700)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._ensure_state_dir()
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(self.lock_path, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _read_owner_unlocked(self) -> dict[str, Any] | None:
        if not self.owner_path.exists():
            return None
        if self.owner_path.is_symlink() or not self.owner_path.is_file():
            raise BrowserLeaseError(f"浏览器租约文件不安全: {self.owner_path}")
        try:
            payload = json.loads(self.owner_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BrowserLeaseError(f"浏览器租约文件损坏: {exc}") from exc
        if not isinstance(payload, dict):
            raise BrowserLeaseError("浏览器租约文件必须是 JSON 对象")
        return payload

    def _write_owner_unlocked(self, owner: dict[str, Any]) -> None:
        temporary = self.state_dir / f".ownership.{os.getpid()}.{secrets.token_hex(6)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(owner, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.owner_path)
            os.chmod(self.owner_path, 0o600)
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> int:
        ttl = int(ttl_seconds)
        if not MIN_TTL_SECONDS <= ttl <= MAX_TTL_SECONDS:
            raise BrowserLeaseError(
                f"租约 TTL 必须在 {MIN_TTL_SECONDS} 到 {MAX_TTL_SECONDS} 秒之间"
            )
        return ttl

    @staticmethod
    def _is_active(owner: dict[str, Any] | None, now: datetime) -> bool:
        if not owner:
            return False
        expires_at = _parse_iso(owner.get("expires_at"))
        return expires_at is not None and expires_at > now

    def acquire(
        self,
        *,
        agent: str,
        task_id: str,
        company: str = "",
        target_id: str = "",
        origin: str = "",
        mode: str = "browser-write",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> dict[str, Any]:
        agent = str(agent or "").strip()
        task_id = str(task_id or "").strip()
        mode = str(mode or "").strip()
        if not agent or not task_id or not mode:
            raise BrowserLeaseError("agent、task_id 和 mode 不能为空")
        ttl = self._validate_ttl(ttl_seconds)
        now = self._now()

        with self._locked():
            previous = self._read_owner_unlocked()
            if self._is_active(previous, now):
                raise BrowserLeaseError(
                    "浏览器已由 "
                    f"{previous.get('agent', 'unknown')} / {previous.get('task_id', 'unknown')} "
                    f"占用至 {previous.get('expires_at', 'unknown')}"
                )

            owner = {
                "schema_version": 1,
                "lease_id": secrets.token_urlsafe(24),
                "agent": agent,
                "task_id": task_id,
                "company": str(company or "").strip(),
                "target_id": str(target_id or "").strip(),
                "origin": _safe_origin(origin),
                "mode": mode,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "acquired_at": _iso(now),
                "heartbeat_at": _iso(now),
                "expires_at": _iso(now + timedelta(seconds=ttl)),
            }
            self._write_owner_unlocked(owner)
            return dict(owner)

    def heartbeat(
        self,
        lease_id: str,
        *,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        target_id: str | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        ttl = self._validate_ttl(ttl_seconds)
        now = self._now()
        with self._locked():
            owner = self._require_owner_unlocked(lease_id, now, require_active=True)
            if target_id is not None:
                owner["target_id"] = str(target_id).strip()
            if mode is not None:
                next_mode = str(mode).strip()
                if not next_mode:
                    raise BrowserLeaseError("mode 不能为空")
                owner["mode"] = next_mode
            owner["heartbeat_at"] = _iso(now)
            owner["expires_at"] = _iso(now + timedelta(seconds=ttl))
            self._write_owner_unlocked(owner)
            return dict(owner)

    def assert_owned(self, lease_id: str) -> dict[str, Any]:
        now = self._now()
        with self._locked():
            return dict(self._require_owner_unlocked(lease_id, now, require_active=True))

    def release(self, lease_id: str) -> dict[str, Any]:
        now = self._now()
        with self._locked():
            owner = self._require_owner_unlocked(lease_id, now, require_active=False)
            self.owner_path.unlink()
            return dict(owner)

    def status(self) -> dict[str, Any]:
        now = self._now()
        with self._locked():
            owner = self._read_owner_unlocked()
            active = self._is_active(owner, now)
            return {
                "active": active,
                "expired": bool(owner) and not active,
                "checked_at": _iso(now),
                "owner": dict(owner) if owner else None,
            }

    def _require_owner_unlocked(
        self,
        lease_id: str,
        now: datetime,
        *,
        require_active: bool,
    ) -> dict[str, Any]:
        token = str(lease_id or "").strip()
        if not token:
            raise BrowserLeaseError("lease_id 不能为空")
        owner = self._read_owner_unlocked()
        if not owner:
            raise BrowserLeaseError("当前没有浏览器租约")
        if not secrets.compare_digest(str(owner.get("lease_id") or ""), token):
            raise BrowserLeaseError("lease_id 与当前浏览器所有者不匹配")
        if require_active and not self._is_active(owner, now):
            raise BrowserLeaseError("浏览器租约已过期，请重新获取")
        return owner


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理共享招聘浏览器的协作式全局租约")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire = subparsers.add_parser("acquire", help="获取浏览器写租约")
    acquire.add_argument("--agent", required=True)
    acquire.add_argument("--task-id", required=True)
    acquire.add_argument("--company", default="")
    acquire.add_argument("--target-id", default="")
    acquire.add_argument("--origin", default="")
    acquire.add_argument("--mode", default="browser-write")
    acquire.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)

    heartbeat = subparsers.add_parser("heartbeat", help="延长当前租约")
    heartbeat.add_argument("--lease-id", required=True)
    heartbeat.add_argument("--target-id")
    heartbeat.add_argument("--mode")
    heartbeat.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)

    release = subparsers.add_parser("release", help="释放当前租约")
    release.add_argument("--lease-id", required=True)

    subparsers.add_parser("status", help="查看当前租约")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manager = BrowserLease(args.state_dir)
    try:
        if args.command == "acquire":
            payload = manager.acquire(
                agent=args.agent,
                task_id=args.task_id,
                company=args.company,
                target_id=args.target_id,
                origin=args.origin,
                mode=args.mode,
                ttl_seconds=args.ttl,
            )
        elif args.command == "heartbeat":
            payload = manager.heartbeat(
                args.lease_id,
                ttl_seconds=args.ttl,
                target_id=args.target_id,
                mode=args.mode,
            )
        elif args.command == "release":
            payload = manager.release(args.lease_id)
        else:
            payload = manager.status()
        _print_json(payload)
        return 0
    except BrowserLeaseError as exc:
        print(f"[browser-lease] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
