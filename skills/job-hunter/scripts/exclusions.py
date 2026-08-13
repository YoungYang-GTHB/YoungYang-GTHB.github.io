"""岗位排除决策库：持久化人工“不投”结论并供扫描器过滤。"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_EXCLUSIONS = (
    PROJECT_ROOT
    / "career"
    / "求职投递"
    / "2027届"
    / "data"
    / "job_exclusions.yaml"
)


def normalize_text(value: Any) -> str:
    return "".join(str(value or "").lower().split())


def normalize_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Aggregated job feeds occasionally place contact instructions such as
    # "邮箱投递：hr@example.com" in a column named “投递地址”.  Such
    # values are useful to the applicant but are not URLs and must not abort a
    # full scan (``urlsplit`` can reject their Unicode pseudo-netloc).
    if not text.lower().startswith(("http://", "https://")):
        return ""
    try:
        parts = urlsplit(text)
    except ValueError:
        return ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


class ExclusionStore:
    """读取、维护和匹配岗位排除规则。"""

    COMPANY_FIELDS = ("企业名称", "公司", "company")
    POSITION_FIELDS = ("职位", "岗位", "title", "position")
    JOB_ID_FIELDS = ("岗位ID", "职位ID", "job_id", "jobAdId")
    URL_FIELDS = ("投递地址", "职位链接", "apply_url", "job_url", "url")

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or DEFAULT_EXCLUSIONS)
        self.data = self._load()

    @property
    def exclusions(self) -> list[dict[str, Any]]:
        return self.data.setdefault("exclusions", [])

    def active_rules(self, phase: str = "") -> list[dict[str, Any]]:
        today = date.today().isoformat()
        rules = []
        for rule in self.exclusions:
            if rule.get("status", "active") != "active":
                continue
            rule_phase = str(rule.get("phase", "")).strip()
            if phase and rule_phase and rule_phase != phase:
                continue
            expires_at = str(rule.get("expires_at", "")).strip()
            if expires_at and expires_at < today:
                continue
            rules.append(rule)
        return rules

    def match(self, job: dict[str, Any], phase: str = "") -> dict[str, Any] | None:
        company = normalize_text(self._first(job, self.COMPANY_FIELDS))
        position = normalize_text(self._first(job, self.POSITION_FIELDS))
        job_id = normalize_text(self._first(job, self.JOB_ID_FIELDS))
        url = normalize_url(self._first(job, self.URL_FIELDS))

        for rule in self.active_rules(phase):
            # 岗位 ID / URL 是强标识；若聚合源没提供强标识，则回退到
            # “公司 + 岗位关键词”，兼容同一岗位在不同平台上的重复链接。
            rule_job_id = normalize_text(rule.get("job_id"))
            rule_url = normalize_url(rule.get("url"))
            if rule_job_id and job_id and rule_job_id == job_id:
                return rule
            if rule_url and url and rule_url == url:
                return rule
            company_rule = normalize_text(rule.get("company"))
            position_rule = normalize_text(rule.get("position_keyword"))
            checks: list[bool] = []
            if company_rule:
                checks.append(company_rule in company)
            if position_rule:
                checks.append(position_rule in position)
            if checks and all(checks):
                return rule
        return None

    def add(self, rule: dict[str, Any]) -> None:
        rule_id = str(rule.get("id", "")).strip()
        if not rule_id:
            raise ValueError("排除规则必须有 id")
        if not any(rule.get(key) for key in ("company", "position_keyword", "job_id", "url")):
            raise ValueError("至少指定 company / position_keyword / job_id / url 之一")
        if any(item.get("id") == rule_id for item in self.exclusions):
            raise ValueError(f"排除规则已存在: {rule_id}")
        normalized = {
            "id": rule_id,
            "company": str(rule.get("company", "")).strip(),
            "position_keyword": str(rule.get("position_keyword", "")).strip(),
            "job_id": str(rule.get("job_id", "")).strip(),
            "url": str(rule.get("url", "")).strip(),
            "phase": str(rule.get("phase", "")).strip(),
            "reason": str(rule.get("reason", "")).strip(),
            "excluded_at": str(rule.get("excluded_at") or date.today().isoformat()),
            "expires_at": str(rule.get("expires_at", "")).strip(),
            "status": "active",
        }
        self.exclusions.append(normalized)
        self.save()

    def disable(self, rule_id: str) -> None:
        for rule in self.exclusions:
            if rule.get("id") == rule_id:
                rule["status"] = "disabled"
                self.save()
                return
        raise ValueError(f"未找到排除规则: {rule_id}")

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        for index, rule in enumerate(self.exclusions):
            prefix = f"exclusions[{index}]"
            rule_id = str(rule.get("id", "")).strip()
            if not rule_id:
                errors.append(f"{prefix}.id 为空")
            elif rule_id in seen:
                errors.append(f"{prefix}.id 重复: {rule_id}")
            seen.add(rule_id)
            if not any(rule.get(key) for key in ("company", "position_keyword", "job_id", "url")):
                errors.append(f"{prefix} 缺少匹配条件")
            if rule.get("status", "active") not in {"active", "disabled"}:
                errors.append(f"{prefix}.status 非法")
        return errors

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = date.today().isoformat()
        self.path.write_text(
            yaml.safe_dump(self.data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "updated_at": date.today().isoformat(), "exclusions": []}
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, dict):
            raise ValueError(f"排除库格式错误: {self.path}")
        payload.setdefault("schema_version", 1)
        payload.setdefault("exclusions", [])
        return payload

    @staticmethod
    def _first(job: dict[str, Any], fields: tuple[str, ...]) -> Any:
        for field in fields:
            if job.get(field) not in (None, ""):
                return job[field]
        return ""
