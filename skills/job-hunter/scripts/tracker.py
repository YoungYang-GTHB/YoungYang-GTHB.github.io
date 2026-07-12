"""
投递记录追踪。

按日期和状态跟踪每一份投递，产出统计报表。
与 fetch/filter 模块零耦合。
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Literal

Status = Literal[
    "matched",     # 系统匹配，待用户确认
    "interested",  # 用户标记感兴趣
    "applied",     # 已投递
    "screening",   # 简历筛选
    "interview",   # 面试中
    "offer",       # 已获 offer
    "rejected",    # 已拒 / 被拒
    "ignored",     # 不感兴趣
]

STATUS_EMOJI = {
    "matched": "🔍",
    "interested": "⭐",
    "applied": "📤",
    "screening": "📋",
    "interview": "🎙️",
    "offer": "🎉",
    "rejected": "❌",
    "ignored": "🗑️",
}


class ApplicationTracker:
    """投递记录管理器。"""

    def __init__(self, records_dir: str | None = None):
        if records_dir is None:
            records_dir = Path(__file__).resolve().parent.parent / "records"
        self._dir = Path(records_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ---- write ----

    def log(
        self,
        company: str,
        position: str,
        status: Status,
        *,
        url: str = "",
        location: str = "",
        resume_version: str = "",
        notes: str = "",
    ) -> None:
        """记录一笔操作。自动追加到当日 CSV。"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = self._dir / f"{date_str}.csv"

        is_new = not filepath.exists()
        with open(filepath, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(
                    [
                        "timestamp", "company", "position", "status",
                        "url", "location", "resume_version", "notes",
                    ]
                )
            writer.writerow(
                [
                    datetime.now().isoformat(), company, position, status,
                    url, location, resume_version, notes,
                ]
            )

    # ---- read / stats ----

    def stats(self, days: int = 30) -> dict:
        """返回最近 N 天的统计。"""
        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = {"dates": {}, "by_status": {}, "total": 0}

        for i in range(days):
            date_str = (cutoff - __import__("datetime").timedelta(days=i)).strftime(
                "%Y-%m-%d"
            )
            filepath = self._dir / f"{date_str}.csv"
            if filepath.exists():
                count = sum(1 for _ in open(filepath, encoding="utf-8")) - 1  # skip header
                if count > 0:
                    result["dates"][date_str] = count
                    result["total"] += count

        return result

    def daily_summary(self, date_str: str = "") -> str:
        """按状态分组输出当日投递摘要。"""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = self._dir / f"{date_str}.csv"
        if not filepath.exists():
            return f"{date_str}: 无投递记录"

        by_status: dict[str, list[dict]] = {}
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("status", "unknown")
                by_status.setdefault(status, []).append(row)

        lines = [f"📊 {date_str} 投递汇总"]
        for status, items in sorted(by_status.items()):
            emoji = STATUS_EMOJI.get(status, "❓")
            lines.append(f"  {emoji} {status}: {len(items)} 条")
        lines.append(f"  ──────────────")
        lines.append(f"  📝 合计: {sum(len(v) for v in by_status.values())} 条")
        return "\n".join(lines)

    def get_recent_companies(self, days: int = 30) -> set[str]:
        """获取最近已投递/已忽略的公司名，用于去重提醒。"""
        cutoff = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                  - __import__("datetime").timedelta(days=days))
        companies: set[str] = set()
        for i in range(days + 1):
            date_str = (cutoff + __import__("datetime").timedelta(days=i)).strftime(
                "%Y-%m-%d"
            )
            filepath = self._dir / f"{date_str}.csv"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("status") in ("applied", "ignored"):
                            companies.add(row.get("company", ""))
        return companies
