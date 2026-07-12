"""
增量抓取状态管理。

记录每个数据源的上次抓取状态，支持：
- 增量模式：仅抓取 更新时间 > last_fetch_time 的记录
- 全量兜底：超过 N 天未全量同步，或记录总数变化 > 阈值，触发全量
- 状态持久化到 state.json（gitignored）
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class FetcherState:
    """管理增量抓取状态，避免每次全量遍历。"""

    def __init__(self, state_path: str | None = None):
        if state_path is None:
            state_path = Path(__file__).resolve().parent.parent / "state.json"
        self._path = Path(state_path)
        self._data: dict = self._load()

    # ---- public API ----

    def should_full_sync(self, nav_id: int) -> bool:
        """是否需要全量同步（首次 / 超过7天 / 上次异常）。"""
        nav_state = self._nav_state(nav_id)
        if not nav_state.get("last_full_sync"):
            return True
        last_full = datetime.fromisoformat(nav_state["last_full_sync"])
        days_since = (datetime.now(timezone.utc) - last_full).days
        return days_since >= 7

    def get_cutoff(self, nav_id: int) -> str | None:
        """
        返回增量抓取的 cutoff 时间（ISO 格式）。
        None 表示需要全量抓取。
        """
        if self.should_full_sync(nav_id):
            return None
        nav_state = self._nav_state(nav_id)
        return nav_state.get("latest_update_time")

    def update(
        self,
        nav_id: int,
        nav_name: str,
        fetched_count: int,
        new_count: int,
        latest_update: str | None = None,
        total_rows: int = 0,
    ) -> None:
        """记录本次抓取结果。"""
        now = datetime.now(timezone.utc).isoformat()
        nav = self._nav_state(nav_id)
        nav["name"] = nav_name
        nav["last_fetch_time"] = now
        nav["last_fetched_count"] = fetched_count
        nav["last_new_count"] = new_count
        nav["total_rows"] = total_rows
        if latest_update:
            nav["latest_update_time"] = latest_update
        if nav.get("last_full_sync") is None or self.should_full_sync(nav_id):
            nav["last_full_sync"] = now
        self._save()

    def check_count_anomaly(self, nav_id: int, current_total: int) -> bool:
        """检测记录总数是否异常变化（>=15%），提示需全量复核。"""
        nav_state = self._nav_state(nav_id)
        prev_total = nav_state.get("total_rows", 0)
        if prev_total == 0:
            return False
        change = abs(current_total - prev_total) / prev_total
        return change >= 0.15

    def mark_applied_job(self, job_url: str) -> None:
        """记录已投递的岗位 URL，用于增量去重。"""
        applied = self._data.setdefault("applied_urls", [])
        if job_url not in applied:
            applied.append(job_url)
            # 只保留最近500条
            self._data["applied_urls"] = applied[-500:]
            self._save()

    def is_applied(self, job_url: str) -> bool:
        return job_url in self._data.get("applied_urls", [])

    def get_summary(self) -> dict:
        """返回所有导航的抓取状态摘要。"""
        summary = {}
        for k, v in self._data.get("navigations", {}).items():
            summary[k] = {
                "name": v.get("name", "?"),
                "last_fetch": v.get("last_fetch_time", "从未"),
                "total_rows": v.get("total_rows", 0),
                "last_new": v.get("last_new_count", 0),
            }
        return summary

    # ---- internal ----

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"navigations": {}, "applied_urls": []}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _nav_state(self, nav_id: int) -> dict:
        navs = self._data.setdefault("navigations", {})
        return navs.setdefault(str(nav_id), {})
