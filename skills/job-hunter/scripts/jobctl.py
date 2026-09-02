#!/usr/bin/env python3
"""统一管理岗位同步、投递门禁、成功记录与汇总渲染。

这个 CLI 不绕过验证码，也不直接点击招聘网站的最终提交按钮。浏览器完成
提交并核验成功后，使用 ``record-applied`` 将结果一次写入统一账本、投递
追踪器和 Offer 去重状态。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = (
    PROJECT_ROOT / "career" / "求职投递" / "2027届" / "data" / "applications.yaml"
)
DEFAULT_SUMMARY = PROJECT_ROOT / "career" / "求职投递" / "2027届" / "投递汇总.md"
DEFAULT_MONITORING = (
    PROJECT_ROOT / "career" / "求职投递" / "2027届" / "data" / "monitoring.yaml"
)

sys.path.insert(0, str(SKILL_ROOT))

from scripts.state import FetcherState
from scripts.tracker import ApplicationTracker
from scripts.exclusions import ExclusionStore


PHASES = {"提前批", "秋招", "春招", "实习", "未知"}
ACTIVE_PHASES = {"提前批", "秋招", "春招"}
STATUSES = {
    "draft",
    "prepared",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
    "held",
}
ACTIVE_APPLICATION_STATUSES = {"applied", "screening", "interview", "offer"}
SUBMISSION_WINDOW_SCOPES = {"company_program"}
POLICY_STATUSES = {
    "current_year_safe",
    "previous_year_evidence",
    "user_exception",
    "unknown",
    "affects_formal",
}
SUBMITTABLE_POLICY_STATUSES = {"current_year_safe", "user_exception"}
POLICY_LABELS = {
    "current_year_safe": "当届明确不影响正式批",
    "previous_year_evidence": "往届规则支持",
    "user_exception": "本人批准例外",
    "unknown": "影响未知",
    "affects_formal": "会影响正式批",
}
STATUS_LABELS = {
    "draft": "草稿",
    "prepared": "待确认",
    "applied": "已投递",
    "screening": "筛选中",
    "interview": "面试中",
    "offer": "Offer",
    "rejected": "已结束",
    "withdrawn": "已撤回",
    "held": "暂缓",
}

# 历史投递记录中的 ``public/resume.pdf`` 是当时的主简历别名；站点重构后
# 文件拆分为 VLA 和嵌入式两个明确版本。保留原始记录文本以便审计，同时让
# 校验使用仍存在的对应版本，避免历史记录阻断后续增量检索。
LEGACY_RESUME_ALIASES = {
    "public/resume.pdf": "public/resume-vla-zh.pdf",
    "public/resume-embedded.pdf": "public/resume-embedded-zh.pdf",
}


class LedgerError(ValueError):
    pass


def resume_file_exists(resume: str) -> bool:
    """Return whether a current or documented legacy resume path is available."""
    candidate = stringify(resume).strip()
    if not candidate:
        return False
    if (PROJECT_ROOT / candidate).is_file():
        return True
    alias = LEGACY_RESUME_ALIASES.get(candidate)
    return bool(alias and (PROJECT_ROOT / alias).is_file())


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses silently shadowed mapping keys."""


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False):
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise LedgerError(
                f"YAML 重复键 {key!r}（第 {key_node.start_mark.line + 1} 行）"
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml_unique(path: Path) -> dict[str, Any]:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader) or {}


def load_monitoring(path: Path = DEFAULT_MONITORING) -> dict[str, Any]:
    if not path.exists():
        raise LedgerError(f"监测清单不存在: {path}")
    payload = load_yaml_unique(path)
    if not isinstance(payload.get("monitors"), list):
        raise LedgerError("monitoring.yaml 的 monitors 必须是列表")
    return payload


def save_monitoring(payload: dict[str, Any], path: Path = DEFAULT_MONITORING) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    temporary.replace(path)


def validate_monitoring(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_statuses = {"watching", "open", "prepared", "tracking"}
    allowed_priorities = {"P0", "P1", "P2"}
    default_resume = stringify(payload.get("default_resume")).strip()
    evidence_cutoff: date | None = None
    updated_at = stringify(payload.get("updated_at")).strip()
    if updated_at:
        try:
            evidence_cutoff = date.fromisoformat(updated_at[:10])
        except ValueError:
            errors.append(f"updated_at 日期无效: {updated_at}")
    if not default_resume:
        errors.append("default_resume 不能为空")
    elif not resume_file_exists(default_resume):
        errors.append(f"default_resume 文件不存在: {default_resume}")
    seen: set[str] = set()
    for index, item in enumerate(payload.get("monitors", []), start=1):
        prefix = f"monitors[{index}]"
        for field in ("id", "company", "status", "priority", "next_check", "action"):
            if not stringify(item.get(field)).strip():
                errors.append(f"{prefix}.{field} 不能为空")
        monitor_id = stringify(item.get("id"))
        if monitor_id in seen:
            errors.append(f"{prefix}.id 重复: {monitor_id}")
        seen.add(monitor_id)
        if item.get("status") not in allowed_statuses:
            errors.append(f"{prefix}.status 非法: {item.get('status')}")
        if item.get("status") == "open" and not stringify(item.get("safe_date")).strip():
            errors.append(f"{prefix}.status 为 open 时 safe_date 不能为空")
        if (
            item.get("status") == "prepared"
            and item.get("priority") in {"P0", "P1"}
            and not stringify(item.get("safe_date")).strip()
        ):
            errors.append(f"{prefix}.P0/P1 prepared 监测项的 safe_date 不能为空")
        if (
            item.get("status") == "prepared"
            and item.get("priority") in {"P0", "P1"}
            and not stringify(item.get("target")).strip()
        ):
            errors.append(f"{prefix}.P0/P1 prepared 监测项的 target 不能为空")
        if (
            item.get("status") in {"open", "prepared"}
            and item.get("priority") in {"P0", "P1"}
            and not stringify(item.get("resume")).strip()
        ):
            errors.append(f"{prefix}.P0/P1 open/prepared 监测项的 resume 不能为空")
        if item.get("status") == "open" and not stringify(item.get("open_confirmed_at")).strip():
            errors.append(f"{prefix}.status 为 open 时 open_confirmed_at 不能为空")
        if item.get("priority") not in allowed_priorities:
            errors.append(f"{prefix}.priority 非法: {item.get('priority')}")
        parsed_dates: dict[str, date] = {}
        for field in (
            "next_check", "safe_date", "hard_deadline", "expected_open", "last_checked", "open_confirmed_at"
        ):
            value = stringify(item.get(field)).strip()
            if not value:
                continue
            try:
                parsed_dates[field] = date.fromisoformat(value)
            except ValueError:
                errors.append(f"{prefix}.{field} 日期无效: {value}")
        deadline_at_value = stringify(item.get("hard_deadline_at")).strip()
        if deadline_at_value:
            try:
                deadline_at = datetime.fromisoformat(deadline_at_value)
            except ValueError:
                errors.append(f"{prefix}.hard_deadline_at 时间无效: {deadline_at_value}")
            else:
                if deadline_at.utcoffset() is None:
                    errors.append(f"{prefix}.hard_deadline_at 必须包含时区偏移")
                if "hard_deadline" not in parsed_dates:
                    errors.append(f"{prefix}.hard_deadline_at 存在时 hard_deadline 不能为空")
                elif deadline_at.date() != parsed_dates["hard_deadline"]:
                    errors.append(f"{prefix}.hard_deadline_at 日期必须与 hard_deadline 一致")
        if (
            "next_check" in parsed_dates
            and "last_checked" in parsed_dates
            and parsed_dates["next_check"] <= parsed_dates["last_checked"]
        ):
            errors.append(f"{prefix}.next_check 必须晚于 last_checked")
        if (
            "safe_date" in parsed_dates
            and "expected_open" in parsed_dates
            and parsed_dates["safe_date"] < parsed_dates["expected_open"]
        ):
            errors.append(f"{prefix}.safe_date 不能早于 expected_open")
        if (
            "safe_date" in parsed_dates
            and "hard_deadline" in parsed_dates
            and parsed_dates["safe_date"] > parsed_dates["hard_deadline"]
        ):
            errors.append(f"{prefix}.safe_date 不能晚于 hard_deadline")
        if (
            "open_confirmed_at" in parsed_dates
            and "last_checked" in parsed_dates
            and parsed_dates["open_confirmed_at"] > parsed_dates["last_checked"]
        ):
            errors.append(f"{prefix}.open_confirmed_at 不能晚于 last_checked")
        action = stringify(item.get("action")).strip()
        action_date_match = re.match(r"^(\d{2}-\d{2})(?!至|起)", action)
        if action_date_match and "next_check" in parsed_dates:
            try:
                action_date = date.fromisoformat(
                    f"{parsed_dates['next_check'].year}-{action_date_match.group(1)}"
                )
            except ValueError:
                errors.append(f"{prefix}.action 起始日期无效: {action_date_match.group(1)}")
            else:
                if action_date != parsed_dates["next_check"]:
                    errors.append(
                        f"{prefix}.action 单次起始日期必须与 next_check 一致: "
                        f"{action_date_match.group(1)} != {parsed_dates['next_check'].strftime('%m-%d')}"
                    )
        if evidence_cutoff is not None:
            for field in ("last_checked", "open_confirmed_at"):
                if field in parsed_dates and parsed_dates[field] > evidence_cutoff:
                    errors.append(
                        f"{prefix}.{field} 不能晚于时间基准 {evidence_cutoff.isoformat()}"
                    )
        if not stringify(item.get("last_checked")).strip():
            errors.append(f"{prefix}.last_checked 不能为空")
        if not stringify(item.get("evidence_status")).strip():
            errors.append(f"{prefix}.evidence_status 不能为空")
        urls = item.get("official_urls")
        if not isinstance(urls, list) or not urls:
            errors.append(f"{prefix}.official_urls 必须是非空列表")
        elif any(not stringify(url).strip() for url in urls):
            errors.append(f"{prefix}.official_urls 不能包含空值")
        if item.get("submit_gate") != "user_confirmation":
            errors.append(f"{prefix}.submit_gate 必须为 user_confirmation")
        application_ids = item.get("application_ids", [])
        if application_ids and not isinstance(application_ids, list):
            errors.append(f"{prefix}.application_ids 必须是列表")
        resume = stringify(item.get("resume") or default_resume).strip()
        if not resume:
            errors.append(f"{prefix}.resume 及 default_resume 不能同时为空")
        elif not resume_file_exists(resume):
            errors.append(f"{prefix}.resume 文件不存在: {resume}")
    return errors


def validate_monitor_coverage(
    ledger: "ApplicationLedger", payload: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    mapped: dict[str, list[str]] = {}
    for monitor in payload.get("monitors", []):
        for application_id in monitor.get("application_ids", []) or []:
            mapped.setdefault(stringify(application_id), []).append(monitor["id"])
    ledger_ids = {stringify(item.get("id")) for item in ledger.applications}
    for application_id, monitor_ids in mapped.items():
        if application_id not in ledger_ids:
            errors.append(
                f"监测项 {','.join(monitor_ids)} 引用了不存在的投递记录: {application_id}"
            )
        if len(monitor_ids) > 1:
            errors.append(
                f"投递记录被多个监测项重复覆盖: {application_id} -> {','.join(monitor_ids)}"
            )
    applications_by_id = {
        stringify(item.get("id")): item for item in ledger.applications
    }
    for monitor in payload.get("monitors", []):
        hard_deadline = stringify(monitor.get("hard_deadline")).strip()
        for application_id in monitor.get("application_ids", []) or []:
            application = applications_by_id.get(stringify(application_id))
            if application is None:
                continue
            application_deadline = stringify(application.get("deadline")).strip()
            exact_application_deadline = False
            if application_deadline:
                try:
                    date.fromisoformat(application_deadline)
                except ValueError:
                    pass
                else:
                    exact_application_deadline = True
            if (
                not hard_deadline
                and exact_application_deadline
                and application.get("status") in {"draft", "prepared", "held"}
            ):
                errors.append(
                    f"投递记录 {application_id} 有明确 deadline {application_deadline}，"
                    f"但监测项 {monitor['id']} 缺少 hard_deadline"
                )
                continue
            if not hard_deadline:
                continue
            if not application_deadline:
                errors.append(
                    f"监测项 {monitor['id']} 有官方硬截止 {hard_deadline}，"
                    f"但投递记录 {application_id} 缺少 deadline"
                )
            elif application_deadline[:10] != hard_deadline:
                errors.append(
                    f"官方硬截止不一致: {monitor['id']}={hard_deadline}, "
                    f"{application_id}={application_deadline}"
                )
    required = {
        stringify(item.get("id"))
        for item in ledger.applications
        if item.get("phase") == "秋招" and item.get("status") in {"prepared", "held"}
    }
    for application_id in sorted(required - set(mapped)):
        errors.append(f"秋招待确认记录缺少监测映射: {application_id}")
    return errors


def monitor_due_reasons(item: dict[str, Any], target: date) -> list[str]:
    """Return all reminder stages that are active on ``target``.

    ``next_check`` remains the recurring/manual check anchor.  Expected opening
    and safety dates additionally produce explicit opening T-7/T-1/day and
    safety T-7/T-3/T-1/day reminders so a single recurring check date cannot
    hide an important stage.
    """
    reasons: list[str] = []
    next_check = date.fromisoformat(stringify(item["next_check"]))
    if next_check == target:
        reasons.append("定期检查")
    elif next_check < target:
        reasons.append(f"检查逾期{(target - next_check).days}天")

    expected_value = stringify(item.get("expected_open")).strip()
    if expected_value and item.get("status") in {"watching", "tracking"}:
        expected_open = date.fromisoformat(expected_value)
        if target == expected_open - timedelta(days=7):
            reasons.append("预计开放前7日")
        if target == expected_open - timedelta(days=1):
            reasons.append("预计开放前1日")
        if target == expected_open:
            reasons.append("预计开放日")
        elif target > expected_open:
            reasons.append(f"预计开放后{(target - expected_open).days}日未确认")

    safe_value = stringify(item.get("safe_date")).strip()
    if safe_value:
        safe_date = date.fromisoformat(safe_value)
        if target == safe_date - timedelta(days=7):
            reasons.append("安全日前7日")
        if target == safe_date - timedelta(days=3):
            reasons.append("安全日前3日")
        if target == safe_date - timedelta(days=2):
            reasons.append("安全日前2日")
        if target == safe_date - timedelta(days=1):
            reasons.append("安全日前1日")
        if target == safe_date:
            reasons.append("安全日")
        elif target > safe_date:
            reasons.append(f"已越过安全日{(target - safe_date).days}天")

    deadline_value = stringify(item.get("hard_deadline")).strip()
    if deadline_value:
        hard_deadline = date.fromisoformat(deadline_value)
        deadline_label = stringify(item.get("deadline_label")).strip() or "官方硬截止"
        days_left = (hard_deadline - target).days
        deadline_at_value = stringify(item.get("hard_deadline_at")).strip()
        deadline_at = datetime.fromisoformat(deadline_at_value) if deadline_at_value else None
        if 1 <= days_left <= 7:
            reasons.append(f"{deadline_label}前{days_left}天")
            if days_left == 1 and deadline_at is not None:
                reasons.append(
                    f"最后可用整日（次日{deadline_at.strftime('%H:%M')}截止）"
                )
        elif days_left == 0:
            if deadline_at is not None and (deadline_at.hour, deadline_at.minute) < (9, 0):
                reasons.append(
                    f"{deadline_label}已于{deadline_at.strftime('%H:%M')}结束（早于09:00日报）"
                )
            else:
                reasons.append(f"{deadline_label}日")
        elif days_left < 0:
            reasons.append(f"已越过{deadline_label}{-days_left}天")

    checked_value = stringify(item.get("last_checked")).strip()
    # Staleness is an evidence-quality qualifier, not a standalone action.
    # Emitting it for every monitor after two days floods the daily queue with
    # records whose own recurrence/opening/safety stage is still in the future.
    # Attach it only after a real reminder stage above has become active.
    if checked_value and reasons:
        checked_date = date.fromisoformat(checked_value)
        age = (target - checked_date).days
        if age >= 2:
            reasons.append(f"官网证据已{age}天未更新")
    confirmed_value = stringify(item.get("open_confirmed_at")).strip()
    if item.get("status") == "open" and confirmed_value:
        confirmed_date = date.fromisoformat(confirmed_value)
        open_age = (target - confirmed_date).days
        if open_age > 0:
            reasons.append(f"确认开放后{open_age}日尚未完成筛岗")
    return reasons


def deadline_display(item: dict[str, Any]) -> str:
    """Render a deadline without discarding an official time or offset."""
    precise = stringify(item.get("hard_deadline_at")).strip()
    if precise:
        return datetime.fromisoformat(precise).isoformat(timespec="minutes").replace("T", " ")
    return stringify(item.get("hard_deadline")).strip() or "—"


def reminder_urgency(reasons: list[str]) -> int:
    """Rank actionable stages independently from company priority.

    A P1 safety deadline must not sit below a P0 routine website check.  The
    company priority remains the second ordering key within the same stage.
    """
    if any("截止" in reason for reason in reasons):
        return -1
    if any(reason == "安全日" or reason.startswith("已越过安全日") for reason in reasons):
        return 0
    if "安全日前1日" in reasons:
        return 1
    if (
        "安全日前3日" in reasons
        or "安全日前2日" in reasons
        or "预计开放前1日" in reasons
        or "预计开放日" in reasons
        or any(reason.startswith("预计开放后") for reason in reasons)
        or any(reason.startswith("确认开放后") for reason in reasons)
    ):
        return 2
    if "安全日前7日" in reasons or "预计开放前7日" in reasons:
        return 3
    if any(reason.startswith("检查逾期") for reason in reasons):
        return 4
    return 5


def select_brief_rows(
    selected: list[tuple[dict[str, Any], list[str]]], limit: int
) -> tuple[
    list[tuple[dict[str, Any], list[str]]],
    list[tuple[dict[str, Any], list[str]]],
]:
    """Keep the brief readable without silently dropping strong reminders.

    Rows at urgency 0-2 are strong reminders.  At most ``limit`` rows receive
    the full evidence/JD/action expansion; additional strong reminders remain
    visible in a compact company-and-reason list.  Routine rows only fill spare
    detailed capacity.
    """
    if len(selected) <= limit:
        return selected, []
    mandatory = [row for row in selected if reminder_urgency(row[1]) <= 2]
    mandatory_ids = {item["id"] for item, _ in mandatory}
    remainder = [row for row in selected if row[0]["id"] not in mandatory_ids]
    detailed_mandatory = mandatory[:limit]
    compact_mandatory = mandatory[limit:]
    detailed = detailed_mandatory + remainder[: max(0, limit - len(detailed_mandatory))]
    return detailed, compact_mandatory


def resume_guidance(item: dict[str, Any]) -> str:
    """Return concise, evidence-bounded resume advice for a selected target."""
    explicit = stringify(item.get("resume_advice"))
    if explicit:
        return explicit
    target_corpus = stringify(item.get("target")).casefold()
    evidence_corpus = stringify(item.get("evidence_status")).casefold()
    # Exact targets are sometimes only opaque ATS IDs (for example J12785).
    # Fall back to verified JD evidence only for those opaque values.  When a
    # target already has a semantic role name, evidence may mention excluded
    # alternatives or optional VLA/infra bonuses and must not override it.
    target_has_semantics = bool(
        re.search(r"[\u4e00-\u9fff]", target_corpus)
        or re.search(r"[a-z]{2,}", target_corpus)
    )
    corpus = target_corpus if target_has_semantics else f"{target_corpus} {evidence_corpus}".strip()
    infra_corpus = f"{corpus} {evidence_corpus}".strip()
    if any(keyword in corpus for keyword in ("具身", "vla", "世界模型", "robot learning", "机器人", "端到端")):
        return (
            "主简历；突出VLA/WAM、双臂真机、ROS2、数据评测闭环与端侧部署；"
            "不虚增Isaac、PPO、双足/步态或量产经验"
        )
    if any(keyword in corpus for keyword in ("多模态", "vlm", "视觉语言")):
        return (
            "主简历；突出多模态/VLA训练、数据与评测、PyTorch、FSDP和部署闭环；"
            "不虚增顶会论文、百亿预训练、生产Agent/RAG或专用领域经验"
        )
    if any(keyword in infra_corpus for keyword in ("训练框架", "训练引擎", "分布式训练", "训练系统", "推理", "infra", "算子", "hpc", "软件栈", "模型部署", "性能优化", "gpu/npu")):
        return (
            "主简历；突出FSDP、Triton、CUDA Graphs、RTC、8倍推理优化与故障定位；"
            "不虚增Megatron、DeepSpeed、vLLM、TensorRT、千卡或编译器核心开发"
        )
    if any(keyword in corpus for keyword in ("多模态", "大模型", "算法", "vlm", "llm")):
        return (
            "主简历；突出多模态/VLA训练、数据与评测、PyTorch、FSDP和部署闭环；"
            "不虚增顶会论文、百亿预训练、生产Agent/RAG或专用领域经验"
        )
    return "主简历；仅使用可验证的项目、训练、性能优化与部署经历，不按JD关键词虚增技能"


def today_string() -> str:
    return date.today().isoformat()


def stringify(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value or "")


def parse_locations(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = str(value or "").replace("，", ",").split(",")
    return [str(item).strip() for item in values if str(item).strip()]


def normalized_identity(value: Any) -> str:
    """Normalize user-facing identifiers for conservative equality checks."""
    return re.sub(r"\s+", "", stringify(value)).casefold()


def applied_date(application: dict[str, Any]) -> date | None:
    value = stringify(application.get("applied_at")).strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def submission_window(application: dict[str, Any]) -> dict[str, Any] | None:
    rule = application.get("submission_window")
    return rule if isinstance(rule, dict) else None


def validate_submission_window(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return [f"{prefix}.submission_window 必须是对象"]
    errors: list[str] = []
    scope = stringify(value.get("scope")).strip()
    if scope not in SUBMISSION_WINDOW_SCOPES:
        errors.append(
            f"{prefix}.submission_window.scope 非法: {scope or '为空'}"
        )
    for field in ("max_applications", "window_days"):
        raw = value.get(field)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            errors.append(
                f"{prefix}.submission_window.{field} 必须是大于等于1的整数"
            )
    return errors


def same_submission_scope(
    candidate: dict[str, Any], previous: dict[str, Any], scope: str
) -> bool:
    if scope != "company_program":
        return False
    return (
        normalized_identity(candidate.get("company"))
        == normalized_identity(previous.get("company"))
        and normalized_identity(candidate.get("program"))
        == normalized_identity(previous.get("program"))
    )


def active_history(
    ledger: "ApplicationLedger", candidate: dict[str, Any], scope: str
) -> list[dict[str, Any]]:
    records = [
        item
        for item in ledger.applications
        if item.get("id") != candidate.get("id")
        and item.get("status") in ACTIVE_APPLICATION_STATUSES
        and same_submission_scope(candidate, item, scope)
    ]
    return sorted(
        records,
        key=lambda item: (stringify(item.get("applied_at")), stringify(item.get("id"))),
        reverse=True,
    )


def effective_submission_window(
    ledger: "ApplicationLedger", candidate: dict[str, Any]
) -> dict[str, Any] | None:
    """Use the candidate rule first, otherwise inherit an active same-project rule."""
    own = submission_window(candidate)
    if own:
        return own
    for item in ledger.applications:
        if item.get("id") == candidate.get("id"):
            continue
        rule = submission_window(item)
        if rule and same_submission_scope(candidate, item, stringify(rule.get("scope"))):
            return rule
    return None


def submission_conflicts(
    ledger: "ApplicationLedger", candidate: dict[str, Any], *, reference: date | None = None
) -> list[str]:
    """Return exact-duplicate and declared application-window conflicts.

    A rule is only enforced when the ledger has an explicit ``submission_window``.
    This avoids inferring a platform limit from vague prose while still making a
    verified company/project rule impossible to overlook.
    """
    conflicts: list[str] = []
    company = normalized_identity(candidate.get("company"))
    candidate_job_id = normalized_identity(candidate.get("job_id"))
    candidate_url = stringify(candidate.get("job_url")).strip().rstrip("/")
    for previous in ledger.applications:
        if previous.get("id") == candidate.get("id"):
            continue
        if previous.get("status") not in ACTIVE_APPLICATION_STATUSES:
            continue
        if normalized_identity(previous.get("company")) != company:
            continue
        same_job_id = bool(candidate_job_id) and (
            candidate_job_id == normalized_identity(previous.get("job_id"))
        )
        previous_url = stringify(previous.get("job_url")).strip().rstrip("/")
        same_url = bool(candidate_url) and candidate_url == previous_url
        if same_job_id or same_url:
            conflicts.append(
                "已存在同一岗位的有效投递："
                f"{previous.get('position')}（{previous.get('id')}，"
                f"{previous.get('applied_at') or '日期未记录'}）"
            )

    rule = effective_submission_window(ledger, candidate)
    if not rule:
        return conflicts
    scope = stringify(rule.get("scope")).strip()
    max_applications = rule.get("max_applications")
    window_days = rule.get("window_days")
    if (
        scope not in SUBMISSION_WINDOW_SCOPES
        or isinstance(max_applications, bool)
        or not isinstance(max_applications, int)
        or isinstance(window_days, bool)
        or not isinstance(window_days, int)
    ):
        return conflicts

    reference_day = reference or date.today()
    cutoff = reference_day - timedelta(days=window_days - 1)
    recent = [
        item
        for item in active_history(ledger, candidate, scope)
        if (item_date := applied_date(item)) is not None and cutoff <= item_date <= reference_day
    ]
    if len(recent) >= max_applications:
        evidence = "；".join(
            f"{item.get('position')}（{item.get('applied_at')}）" for item in recent
        )
        conflicts.append(
            f"公司/项目投递窗口已满：{scope} 在 {window_days} 天内最多 "
            f"{max_applications} 个有效职位；已有 {len(recent)} 个：{evidence}"
        )
    return conflicts


def history_records(
    ledger: "ApplicationLedger",
    *,
    company: str = "",
    program: str = "",
    job_id: str = "",
    url: str = "",
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """Filter all ledger records for the pre-submission history table."""
    company_key = normalized_identity(company)
    program_key = normalized_identity(program)
    job_key = normalized_identity(job_id)
    url_key = stringify(url).strip().rstrip("/")
    records: list[dict[str, Any]] = []
    for item in ledger.applications:
        if company_key and company_key not in normalized_identity(item.get("company")):
            continue
        if program_key and program_key not in normalized_identity(item.get("program")):
            continue
        if job_key and job_key != normalized_identity(item.get("job_id")):
            continue
        if url_key and url_key != stringify(item.get("job_url")).strip().rstrip("/"):
            continue
        if active_only and item.get("status") not in ACTIVE_APPLICATION_STATUSES:
            continue
        records.append(item)
    return sorted(
        records,
        key=lambda item: (stringify(item.get("applied_at")), stringify(item.get("id"))),
        reverse=True,
    )


def render_history_table(records: list[dict[str, Any]]) -> str:
    lines = [
        "| 状态 | 投递日期 | 公司 | 项目 | 岗位 | 岗位 ID | 记录 ID |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in records:
        clean = lambda value: stringify(value).replace("|", "\\|").replace("\n", " ")
        lines.append(
            "| "
            + " | ".join(
                (
                    STATUS_LABELS.get(clean(item.get("status")), clean(item.get("status"))),
                    clean(item.get("applied_at")) or "—",
                    clean(item.get("company")),
                    clean(item.get("program")) or "—",
                    clean(item.get("position")),
                    clean(item.get("job_id")) or "—",
                    clean(item.get("id")),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def confirmation_token(application: dict[str, Any]) -> str:
    stable = {
        key: application.get(key, "")
        for key in (
            "id",
            "company",
            "program",
            "position",
            "job_id",
            "phase",
            "policy_status",
            "job_url",
            "resume",
            "locations",
            "channel",
        )
    }
    digest = hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return f"CONFIRM:{application.get('id', 'unknown')}:{digest}"


class ApplicationLedger:
    def __init__(self, path: Path = DEFAULT_LEDGER):
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": today_string(),
                "applications": [],
            }
        payload = load_yaml_unique(self.path)
        payload.setdefault("schema_version", 1)
        payload.setdefault("active_phase", "提前批")
        payload.setdefault("updated_at", today_string())
        payload.setdefault("applications", [])
        if not isinstance(payload["applications"], list):
            raise LedgerError("applications 必须是列表")
        return payload

    @property
    def applications(self) -> list[dict[str, Any]]:
        return self.data["applications"]

    def get(self, application_id: str) -> dict[str, Any]:
        for item in self.applications:
            if item.get("id") == application_id:
                return item
        raise LedgerError(f"未找到投递记录: {application_id}")

    def upsert(self, application: dict[str, Any], *, allow_update: bool = False) -> None:
        for index, item in enumerate(self.applications):
            if item.get("id") != application.get("id"):
                continue
            if not allow_update:
                raise LedgerError(f"记录已存在: {application.get('id')}")
            self.applications[index] = application
            return
        self.applications.append(application)

    def validate(self) -> list[str]:
        errors: list[str] = []
        evidence_cutoff: date | None = None
        updated_at = stringify(self.data.get("updated_at")).strip()
        if updated_at:
            try:
                evidence_cutoff = date.fromisoformat(updated_at[:10])
            except ValueError:
                errors.append(f"updated_at 日期无效: {updated_at}")
        if self.data.get("active_phase") not in ACTIVE_PHASES:
            errors.append(f"active_phase 非法: {self.data.get('active_phase')}")
        seen_ids: set[str] = set()
        for index, item in enumerate(self.applications, start=1):
            prefix = f"applications[{index}]"
            for field in ("id", "company", "position", "phase", "status", "policy_status"):
                if not stringify(item.get(field)).strip():
                    errors.append(f"{prefix}.{field} 不能为空")
            app_id = stringify(item.get("id"))
            if app_id in seen_ids:
                errors.append(f"{prefix}.id 重复: {app_id}")
            seen_ids.add(app_id)
            if item.get("phase") not in PHASES:
                errors.append(f"{prefix}.phase 非法: {item.get('phase')}")
            if item.get("status") not in STATUSES:
                errors.append(f"{prefix}.status 非法: {item.get('status')}")
            if item.get("policy_status") not in POLICY_STATUSES:
                errors.append(f"{prefix}.policy_status 非法: {item.get('policy_status')}")
            errors.extend(validate_submission_window(item.get("submission_window"), prefix))
            if item.get("status") in {"applied", "screening", "interview", "offer"}:
                for field in ("applied_at", "channel", "resume"):
                    if not stringify(item.get(field)).strip():
                        errors.append(f"{prefix}.{field} 在已投递状态下不能为空")
            applied_at = stringify(item.get("applied_at")).strip()
            if applied_at and evidence_cutoff is not None:
                try:
                    applied_date = date.fromisoformat(applied_at[:10])
                except ValueError:
                    errors.append(f"{prefix}.applied_at 日期无效: {applied_at}")
                else:
                    if applied_date > evidence_cutoff:
                        errors.append(
                            f"{prefix}.applied_at 不能晚于时间基准 {evidence_cutoff.isoformat()}"
                        )
            resume = stringify(item.get("resume"))
            if resume and not resume_file_exists(resume):
                errors.append(f"{prefix}.resume 文件不存在: {resume}")
        return errors

    def save(self) -> None:
        errors = self.validate()
        if errors:
            raise LedgerError("账本校验失败:\n- " + "\n- ".join(errors))
        self.data["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            yaml.safe_dump(
                self.data,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            ),
            encoding="utf-8",
        )
        os.replace(temp_path, self.path)


def render_summary(ledger: ApplicationLedger, output_path: Path = DEFAULT_SUMMARY) -> str:
    applications = sorted(
        ledger.applications,
        key=lambda item: (stringify(item.get("applied_at")), stringify(item.get("id"))),
        reverse=True,
    )
    applied = [item for item in applications if item.get("status") in {"applied", "screening", "interview", "offer"}]
    companies = {item.get("company") for item in applied if item.get("company")}
    status_counts = Counter(item.get("status") for item in applications)
    policy_counts = Counter(item.get("policy_status") for item in applications)

    lines = [
        "# 2027 届投递汇总",
        "",
        "> 本文件由 `python3 skills/job-hunter/scripts/jobctl.py render` 自动生成，请修改 `data/applications.yaml`，不要手工维护本表。",
        "",
        f"- 已投递：**{len(applied)} 个岗位 / {len(companies)} 家公司**",
        f"- 当前批次：**{ledger.data.get('active_phase')}**",
        "- 状态：" + "；".join(
            f"{STATUS_LABELS.get(key, key)} {value}" for key, value in sorted(status_counts.items())
        ),
        "- 批次政策：" + "；".join(
            f"{POLICY_LABELS.get(key, key)} {value}" for key, value in sorted(policy_counts.items())
        ),
        f"- 更新时间：{stringify(ledger.data.get('updated_at'))}",
        "",
        "| 公司 | 岗位 | 批次 | 政策口径 | 状态 | 投递日期 | 渠道 | 城市 | 简历 | 核验 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in applications:
        locations = "、".join(parse_locations(item.get("locations", []))) or "—"
        verified = "已核验" if item.get("record_verified") else "待核验"
        lines.append(
            "| {company} | {position} | {phase} | {policy} | {status} | {date} | {channel} | {locations} | `{resume}` | {verified} |".format(
                company=item.get("company", "—"),
                position=item.get("position", "—"),
                phase=item.get("phase", "—"),
                policy=POLICY_LABELS.get(item.get("policy_status"), item.get("policy_status", "—")),
                status=STATUS_LABELS.get(item.get("status"), item.get("status", "—")),
                date=stringify(item.get("applied_at")) or "—",
                channel=item.get("channel", "—"),
                locations=locations,
                resume=item.get("resume", "—"),
                verified=verified,
            )
        )
    lines.append("")
    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


def cmd_status(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    errors = ledger.validate()
    if errors:
        print("账本校验失败:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    status_counts = Counter(item.get("status") for item in ledger.applications)
    applied = [item for item in ledger.applications if item.get("status") in {"applied", "screening", "interview", "offer"}]
    print(f"账本: {ledger.path}")
    print(f"当前批次: {ledger.data.get('active_phase')}")
    print(f"记录: {len(ledger.applications)}；已投递: {len(applied)}；公司: {len({item.get('company') for item in applied})}")
    for status, count in sorted(status_counts.items()):
        print(f"  {STATUS_LABELS.get(status, status)}: {count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    errors = ledger.validate()
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    monitoring = load_monitoring(Path(args.monitoring))
    monitor_errors = validate_monitoring(monitoring)
    monitor_errors.extend(validate_monitor_coverage(ledger, monitoring))
    if monitor_errors:
        for error in monitor_errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"[jobctl] 校验通过：投递账本 {len(ledger.applications)} 条；"
        f"监测项 {len(monitoring.get('monitors', []))} 条"
    )
    return 0


def cmd_monitor_due(args: argparse.Namespace) -> int:
    path = Path(args.monitoring)
    payload = load_monitoring(path)
    errors = validate_monitoring(payload)
    if errors:
        raise LedgerError("监测清单校验失败:\n- " + "\n- ".join(errors))
    timezone_name = stringify(payload.get("timezone")) or "Asia/Shanghai"
    target = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ZoneInfo(timezone_name)).date()
    )
    monitors = payload["monitors"]
    with_reasons = [(item, monitor_due_reasons(item, target)) for item in monitors]
    selected = with_reasons if args.all else [
        (item, reasons) for item, reasons in with_reasons if reasons
    ]
    selected.sort(
        key=lambda row: (
            reminder_urgency(row[1]),
            {"P0": 0, "P1": 1, "P2": 2}[row[0]["priority"]],
            row[0].get("hard_deadline") or "9999-12-31",
            row[0].get("safe_date") or "9999-12-31",
            row[0]["next_check"],
            row[0]["company"],
        )
    )
    total_selected = len(selected)
    compact_mandatory: list[tuple[dict[str, Any], list[str]]] = []
    if args.brief and total_selected > args.brief_limit:
        selected, compact_mandatory = select_brief_rows(selected, args.brief_limit)
    print(f"监测日期: {target.isoformat()}；到期 {total_selected} / {len(monitors)}")
    if args.brief:
        hidden = total_selected - len(selected) - len(compact_mandatory)
        print(
            f"行动简报: 详列 {len(selected)} 项；紧凑强提醒 {len(compact_mandatory)} 项；"
            f"后台巡检保留 {hidden} 项；强提醒以详表或紧凑清单保留"
        )
        if compact_mandatory:
            print("其余强提醒（公司｜原因）:")
            for start in range(0, len(compact_mandatory), 6):
                chunk = compact_mandatory[start : start + 6]
                print(
                    "；".join(
                        f"{item['company']}｜{'、'.join(reasons)}"
                        for item, reasons in chunk
                    )
                )
    default_resume = stringify(payload.get("default_resume"))
    print(
        "优先级\t提醒原因\t下次检查\t安全日\t截止节点\t公司\t状态\t"
        "最后核验\t官网证据状态\t推荐岗位\t简历\t简历建议\t动作"
    )
    for item, reasons in selected:
        print(
            f"{item['priority']}\t{'、'.join(reasons) or '尚未到期'}\t"
            f"{item['next_check']}\t"
            f"{item.get('safe_date') or '—'}\t{deadline_display(item)}\t{item['company']}\t"
            f"{item['status']}\t{item.get('last_checked') or '—'}\t"
            f"{item.get('evidence_status') or '待下次官网核验'}\t"
            f"{item.get('target') or '待开放后筛选'}\t"
            f"{item.get('resume') or default_resume}\t{resume_guidance(item)}\t{item['action']}"
        )
    return 0


def cmd_monitor_record_check(args: argparse.Namespace) -> int:
    """Record one evidence-backed website check and move its recurrence date."""
    path = Path(args.monitoring)
    payload = load_monitoring(path)
    errors = validate_monitoring(payload)
    if errors:
        raise LedgerError("监测清单校验失败:\n- " + "\n- ".join(errors))
    timezone_name = stringify(payload.get("timezone")) or "Asia/Shanghai"
    checked = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ZoneInfo(timezone_name)).date()
    )
    next_check = date.fromisoformat(args.next_check)
    if next_check <= checked:
        raise LedgerError("--next-check 必须晚于本次核验日期，避免任务立即再次逾期")
    monitor = next(
        (item for item in payload["monitors"] if stringify(item.get("id")) == args.id),
        None,
    )
    if monitor is None:
        raise LedgerError(f"监测项不存在: {args.id}")
    monitor["last_checked"] = checked.isoformat()
    monitor["evidence_status"] = args.evidence.strip()
    monitor["next_check"] = next_check.isoformat()
    if args.status:
        monitor["status"] = args.status
    if args.safe_date is not None:
        monitor["safe_date"] = args.safe_date
    if args.expected_open is not None:
        monitor["expected_open"] = args.expected_open
    if monitor["status"] == "open":
        if not stringify(monitor.get("open_confirmed_at")).strip():
            monitor["open_confirmed_at"] = checked.isoformat()
        if next_check > checked + timedelta(days=3):
            raise LedgerError(
                "状态为 open 时 --next-check 最迟为开放后 3 日，"
                "以保证及时完成全量筛岗"
            )
        if args.safe_date is None and not stringify(monitor.get("safe_date")).strip():
            monitor["safe_date"] = (checked + timedelta(days=7)).isoformat()
    payload["updated_at"] = datetime.now(ZoneInfo(timezone_name)).isoformat(timespec="seconds")
    errors = validate_monitoring(payload)
    if errors:
        raise LedgerError("更新后监测清单校验失败:\n- " + "\n- ".join(errors))
    save_monitoring(payload, path)
    print(
        f"[jobctl] 已记录官网核验: {monitor['company']} ({args.id})；"
        f"{checked.isoformat()} → 下次 {next_check.isoformat()}；状态 {monitor['status']}"
    )
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    if args.phase != ledger.data.get("active_phase"):
        raise LedgerError(
            f"当前批次是 {ledger.data.get('active_phase')}，不能准备 {args.phase} 岗位"
        )
    if args.update:
        try:
            existing = ledger.get(args.id)
        except LedgerError:
            existing = None
        if existing and existing.get("status") in {"applied", "screening", "interview", "offer"}:
            raise LedgerError(f"{args.id} 已进入投递流程，不能用 prepare 覆盖")

    application = {
        "id": args.id,
        "company": args.company,
        "program": args.program or "",
        "position": args.position,
        "job_id": args.job_id or "",
        "phase": args.phase,
        "policy_status": args.policy_status,
        "policy_evidence": args.policy_evidence or "",
        "status": (
            "prepared" if args.policy_status in SUBMITTABLE_POLICY_STATUSES else "held"
        ),
        "deadline": args.deadline or "",
        "job_url": args.job_url or "",
        "locations": parse_locations(args.locations),
        "resume": args.resume,
        "channel": args.channel,
        "referral_code": args.referral_code or "",
        "record_verified": False,
        "notes": args.notes or "",
    }
    ledger.upsert(application, allow_update=args.update)
    ledger.save()
    print(f"[jobctl] 已准备: {application['id']}")
    if application["status"] == "prepared":
        print(f"[jobctl] 确认令牌: {confirmation_token(application)}")
    else:
        print(
            "[jobctl] 已留档并暂缓：需要当届不影响正式批的明确证据，"
            "或本人明确批准例外后才能进入 preflight"
        )
    return 0


def cmd_set_phase(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    previous = ledger.data.get("active_phase")
    ledger.data["active_phase"] = args.phase
    ledger.save()
    print(f"[jobctl] 当前批次: {previous} → {args.phase}")
    return 0


def print_preflight(ledger: ApplicationLedger, application: dict[str, Any]) -> None:
    print("=== 投递前检查 ===")
    print(f"记录 ID: {application.get('id')}")
    print(f"公司 / 项目: {application.get('company')} / {application.get('program') or '—'}")
    print(f"岗位: {application.get('position')} ({application.get('job_id') or '无岗位 ID'})")
    print(f"批次: {application.get('phase')}")
    print(f"政策: {POLICY_LABELS.get(application.get('policy_status'), application.get('policy_status'))}")
    print(f"简历: {application.get('resume')}")
    print(f"城市: {'、'.join(parse_locations(application.get('locations', []))) or '—'}")
    print(f"渠道: {application.get('channel') or '—'}")
    print(f"内推码: {application.get('referral_code') or '无'}")
    print(f"岗位链接: {application.get('job_url') or '—'}")
    rule = effective_submission_window(ledger, application)
    if rule:
        print(
            "公司/项目窗口: "
            f"{rule.get('scope')}，{rule.get('window_days')} 天内最多 "
            f"{rule.get('max_applications')} 个职位"
        )
    history = active_history(ledger, application, "company_program")
    if history:
        print("同公司同项目有效投递:")
        for item in history:
            print(
                f"- {item.get('position')} ({item.get('job_id') or '无岗位ID'}) / "
                f"{item.get('status')} / {item.get('applied_at') or '日期未记录'}"
            )
    else:
        print("同公司同项目有效投递: 无")
    print(f"确认令牌: {confirmation_token(application)}")
    print("说明: 此令牌只用于记录本人已确认；验证码和招聘网站最终提交仍由浏览器流程处理。")


def ensure_submittable(ledger: ApplicationLedger, application: dict[str, Any]) -> None:
    active_phase = ledger.data.get("active_phase")
    if application.get("phase") != active_phase:
        raise LedgerError(
            f"当前只投 {active_phase}，该岗位属于 {application.get('phase')}，已阻止进入提交流程"
        )
    conflicts = submission_conflicts(ledger, application)
    if conflicts:
        raise LedgerError("投递前去重阻断:\n- " + "\n- ".join(conflicts))
    if application.get("status") != "prepared":
        raise LedgerError(
            f"当前记录状态为“{STATUS_LABELS.get(application.get('status'), application.get('status'))}”，"
            "只有待确认岗位才能进入提交前检查"
        )
    policy_status = application.get("policy_status")
    if policy_status not in SUBMITTABLE_POLICY_STATUSES:
        raise LedgerError(
            f"政策状态为“{POLICY_LABELS.get(policy_status, policy_status)}”，"
            "不能直接提交；取得当届明确证据或本人批准例外后再更新账本"
        )


def cmd_preflight(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    application = ledger.get(args.id)
    ensure_submittable(ledger, application)
    print_preflight(ledger, application)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    if not any((args.company, args.program, args.job_id, args.url)):
        raise LedgerError("history 至少需要 --company、--program、--job-id 或 --url 中的一项")
    ledger = ApplicationLedger(Path(args.ledger))
    records = history_records(
        ledger,
        company=args.company,
        program=args.program,
        job_id=args.job_id,
        url=args.url,
        active_only=args.active_only,
    )
    if args.limit:
        records = records[: args.limit]
    content = render_history_table(records)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"[jobctl] 已写入投递历史表: {output}")
    else:
        print(content, end="")
    return 0


def cmd_record_applied(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    application = ledger.get(args.id)
    ensure_submittable(ledger, application)
    expected = confirmation_token(application)
    if args.confirmation != expected:
        raise LedgerError("确认令牌不匹配；请重新运行 preflight 获取当前令牌")
    if application.get("status") not in {"draft", "prepared"}:
        raise LedgerError(f"当前状态不允许记录提交: {application.get('status')}")

    application["status"] = "applied"
    application["applied_at"] = args.applied_at or today_string()
    application["channel"] = args.channel or application.get("channel") or "官网投递"
    application["record_verified"] = bool(args.verified)
    application["proof"] = args.proof or ""
    if args.notes:
        application["notes"] = args.notes
    ledger.save()

    tracker = ApplicationTracker()
    tracker.log(
        company=application.get("company", ""),
        position=application.get("position", ""),
        status="applied",
        application_id=application.get("id", ""),
        url=application.get("job_url", ""),
        location="、".join(parse_locations(application.get("locations", []))),
        resume_version=application.get("resume", ""),
        notes=application.get("notes", ""),
    )
    if application.get("job_url"):
        FetcherState().mark_applied_job(application["job_url"])
    render_summary(ledger, Path(args.summary))
    print(f"[jobctl] 已记录投递成功: {application['id']}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """把统一账本幂等同步到旧追踪器、URL 去重状态和 Markdown 汇总。"""
    ledger = ApplicationLedger(Path(args.ledger))
    errors = ledger.validate()
    if errors:
        raise LedgerError("账本校验失败:\n- " + "\n- ".join(errors))
    tracker = ApplicationTracker()
    state = FetcherState()
    logged = 0
    marked = 0
    for application in ledger.applications:
        if application.get("status") not in {"applied", "screening", "interview", "offer"}:
            continue
        if tracker.log(
            company=application.get("company", ""),
            position=application.get("position", ""),
            status="applied",
            application_id=application.get("id", ""),
            url=application.get("job_url", ""),
            location="、".join(parse_locations(application.get("locations", []))),
            resume_version=application.get("resume", ""),
            notes=application.get("notes", ""),
        ):
            logged += 1
        if application.get("job_url") and not state.is_applied(application["job_url"]):
            state.mark_applied_job(application["job_url"])
            marked += 1
    render_summary(ledger, Path(args.summary))
    print(f"[jobctl] 对账完成：新增追踪记录 {logged}，新增去重 URL {marked}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    ledger = ApplicationLedger(Path(args.ledger))
    output = Path(args.output)
    render_summary(ledger, output)
    print(f"[jobctl] 已生成: {output}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    phase = args.phase or ApplicationLedger(Path(args.ledger)).data.get("active_phase")
    if args.browser_export:
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "import_offer_export.py"),
            "--input",
            args.browser_export,
            "--phase",
            phase,
        ]
        if args.output:
            command += ["--output", args.output]
        if args.dry_run:
            command.append("--dry-run")
        return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode

    command = [sys.executable, str(SKILL_ROOT / "scripts" / "fetch_jobs.py")]
    if args.nav:
        command += ["--nav", str(args.nav)]
    if args.full_sync:
        command.append("--full-sync")
    command += ["--phase", phase]
    if args.dry_run:
        command.append("--dry-run")
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def find_latest_pool(phase: str) -> Path:
    phase_file = {"提前批": "advance", "秋招": "autumn", "春招": "spring"}[phase]
    candidates = sorted((PROJECT_ROOT / "output").glob(f"*-offer-{phase_file}-jobs.jsonl"))
    if not candidates:
        raise LedgerError(f"未找到 {phase} 岗位池；请先运行 jobctl sync 或导入浏览器导出文件")
    return candidates[-1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as error:
                raise LedgerError(f"{path}:{line_number} JSON 无效: {error}") from error
            if isinstance(value, dict):
                records.append(value)
    return records


def cmd_shortlist(args: argparse.Namespace) -> int:
    phase = args.phase or ApplicationLedger(Path(args.ledger)).data.get("active_phase")
    input_path = Path(args.input) if args.input else find_latest_pool(phase)
    records = load_jsonl(input_path)
    records.sort(
        key=lambda item: (
            int(item.get("_match_score", 0) or 0),
            stringify(item.get("更新时间")),
        ),
        reverse=True,
    )
    qualified = [
        item
        for item in records
        if int(item.get("_match_score", 0) or 0) >= args.min_score
    ]
    selected = qualified[: args.limit] if args.limit > 0 else qualified
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0
    print(
        f"岗位池: {input_path}；共 {len(records)} 条；"
        f"分数≥{args.min_score} 的 {len(qualified)} 条；显示 {len(selected)} 条"
    )
    print("分数\t主线\t公司\t岗位\t地点\t截止时间\t匹配依据")
    for item in selected:
        reasons = ",".join(item.get("_match_reasons", []))
        print(
            "{score}\t{track}\t{company}\t{position}\t{location}\t{deadline}\t{reasons}".format(
                score=item.get("_match_score", 0),
                track=item.get("_target_track", "观察"),
                company=item.get("企业名称", ""),
                position=item.get("职位", ""),
                location=item.get("工作地点", ""),
                deadline=item.get("截止时间", ""),
                reasons=reasons,
            )
        )
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """增量同步 Offer 情报局，并只打印紧凑的高匹配新增岗位。"""
    phase = args.phase or ApplicationLedger(Path(args.ledger)).data.get("active_phase")
    command = [
        sys.executable,
        str(SKILL_ROOT / "scripts" / "fetch_jobs.py"),
        "--phase",
        phase,
    ]
    if args.nav:
        command += ["--nav", str(args.nav)]
    if args.full_sync:
        command.append("--full-sync")
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode:
        return result.returncode
    return cmd_shortlist(
        argparse.Namespace(
            phase=phase,
            input="",
            limit=args.limit,
            min_score=args.min_score,
            json=args.json,
            ledger=args.ledger,
        )
    )


def cmd_exclude_add(args: argparse.Namespace) -> int:
    store = ExclusionStore(args.exclusions)
    store.add(
        {
            "id": args.id,
            "company": args.company,
            "position_keyword": args.position_keyword,
            "job_id": args.job_id,
            "url": args.url,
            "phase": args.phase,
            "reason": args.reason,
            "expires_at": args.expires_at,
        }
    )
    print(f"[jobctl] 已加入排除库: {args.id}")
    return 0


def cmd_exclude_list(args: argparse.Namespace) -> int:
    store = ExclusionStore(args.exclusions)
    rules = store.active_rules(args.phase)
    print(f"排除库: {store.path}；生效规则 {len(rules)} 条")
    print("ID\t阶段\t公司\t岗位关键词/岗位ID\t理由")
    for rule in rules:
        target = rule.get("position_keyword") or rule.get("job_id") or rule.get("url")
        print(
            f"{rule.get('id')}\t{rule.get('phase') or '全部'}\t"
            f"{rule.get('company')}\t{target}\t{rule.get('reason')}"
        )
    return 0


def cmd_exclude_remove(args: argparse.Namespace) -> int:
    store = ExclusionStore(args.exclusions)
    store.disable(args.id)
    print(f"[jobctl] 已停用排除规则: {args.id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="统一投递账本路径")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="查看统一投递统计")
    status_parser.set_defaults(handler=cmd_status)

    validate_parser = subparsers.add_parser("validate", help="校验账本和简历文件")
    validate_parser.add_argument("--monitoring", default=str(DEFAULT_MONITORING))
    validate_parser.set_defaults(handler=cmd_validate)

    monitor_parser = subparsers.add_parser("monitor-due", help="列出指定日期已到期的官网监测动作")
    monitor_parser.add_argument("--date", default="", help="YYYY-MM-DD；默认系统当天")
    monitor_parser.add_argument("--all", action="store_true", help="显示全部监测项")
    monitor_parser.add_argument(
        "--brief", action="store_true", help="显示人工行动简报，但不截断安全日/T-1/已开放未筛岗"
    )
    monitor_parser.add_argument(
        "--brief-limit", type=int, default=12, help="简报的常规目标条数，默认 12"
    )
    monitor_parser.add_argument("--monitoring", default=str(DEFAULT_MONITORING))
    monitor_parser.set_defaults(handler=cmd_monitor_due)

    monitor_record_parser = subparsers.add_parser(
        "monitor-record-check", help="记录一次官网核验并设置下一次检查日期（不投递）"
    )
    monitor_record_parser.add_argument("id", help="monitoring.yaml 中的监测项 ID")
    monitor_record_parser.add_argument("--evidence", required=True, help="本次官网核验结论")
    monitor_record_parser.add_argument("--next-check", required=True, help="下一次检查日 YYYY-MM-DD")
    monitor_record_parser.add_argument("--date", default="", help="本次核验日；默认北京时间当天")
    monitor_record_parser.add_argument(
        "--status", choices=("watching", "open", "prepared", "tracking"), default=""
    )
    monitor_record_parser.add_argument(
        "--safe-date", default=None, help="可选更新安全日；传空字符串可清除"
    )
    monitor_record_parser.add_argument(
        "--expected-open", default=None, help="可选更新预计开放日；传空字符串可清除"
    )
    monitor_record_parser.add_argument("--monitoring", default=str(DEFAULT_MONITORING))
    monitor_record_parser.set_defaults(handler=cmd_monitor_record_check)

    phase_parser = subparsers.add_parser("set-phase", help="切换当前允许投递的招聘批次")
    phase_parser.add_argument("phase", choices=("提前批", "秋招", "春招"))
    phase_parser.set_defaults(handler=cmd_set_phase)

    prepare_parser = subparsers.add_parser("prepare", help="创建投递草稿并生成确认令牌")
    prepare_parser.add_argument("--id", required=True)
    prepare_parser.add_argument("--company", required=True)
    prepare_parser.add_argument("--program", default="")
    prepare_parser.add_argument("--position", required=True)
    prepare_parser.add_argument("--job-id", default="")
    prepare_parser.add_argument("--phase", choices=sorted(PHASES), required=True)
    prepare_parser.add_argument("--policy-status", choices=sorted(POLICY_STATUSES), required=True)
    prepare_parser.add_argument("--policy-evidence", default="")
    prepare_parser.add_argument("--deadline", default="")
    prepare_parser.add_argument("--job-url", default="")
    prepare_parser.add_argument("--locations", default="")
    prepare_parser.add_argument("--resume", default="public/resume.pdf")
    prepare_parser.add_argument("--channel", default="官网投递")
    prepare_parser.add_argument("--referral-code", default="")
    prepare_parser.add_argument("--notes", default="")
    prepare_parser.add_argument("--update", action="store_true")
    prepare_parser.set_defaults(handler=cmd_prepare)

    preflight_parser = subparsers.add_parser("preflight", help="显示最终提交前快照和确认令牌")
    preflight_parser.add_argument("id")
    preflight_parser.set_defaults(handler=cmd_preflight)

    history_parser = subparsers.add_parser(
        "history", help="查询公司/项目/岗位的历史投递，供提交前去重"
    )
    history_parser.add_argument("--company", default="", help="公司名，可使用部分名称")
    history_parser.add_argument("--program", default="", help="招聘项目名，可使用部分名称")
    history_parser.add_argument("--job-id", default="", help="精确岗位 ID")
    history_parser.add_argument("--url", default="", help="精确岗位链接")
    history_parser.add_argument(
        "--active-only", action="store_true", help="只显示已投递/筛选/面试/Offer 记录"
    )
    history_parser.add_argument("--limit", type=int, default=0, help="最多显示的记录数；0 表示全部")
    history_parser.add_argument("--output", default="", help="可选 Markdown 表格输出路径")
    history_parser.set_defaults(handler=cmd_history)

    applied_parser = subparsers.add_parser("record-applied", help="浏览器提交成功后统一落档")
    applied_parser.add_argument("id")
    applied_parser.add_argument("--confirmation", required=True)
    applied_parser.add_argument("--applied-at", default="")
    applied_parser.add_argument("--channel", default="")
    applied_parser.add_argument("--verified", action="store_true")
    applied_parser.add_argument("--proof", default="")
    applied_parser.add_argument("--notes", default="")
    applied_parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    applied_parser.set_defaults(handler=cmd_record_applied)

    reconcile_parser = subparsers.add_parser("reconcile", help="从统一账本幂等回填追踪器、去重状态和汇总")
    reconcile_parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    render_parser = subparsers.add_parser("render", help="从账本生成 Markdown 汇总")
    render_parser.add_argument("--output", default=str(DEFAULT_SUMMARY))
    render_parser.set_defaults(handler=cmd_render)

    sync_parser = subparsers.add_parser(
        "sync", help="同步 Offer 情报局；支持会话直连或浏览器导出兜底"
    )
    sync_parser.add_argument("--nav", type=int, default=61)
    sync_parser.add_argument(
        "--phase", choices=("提前批", "秋招", "春招"), default="",
        help="默认读取统一账本的 active_phase",
    )
    sync_parser.add_argument(
        "--browser-export",
        default="",
        help="直连不可用时导入浏览器扩展生成的 raw.jsonl",
    )
    sync_parser.add_argument("--output", default="", help="浏览器导入模式的输出路径")
    sync_parser.add_argument("--full-sync", action="store_true")
    sync_parser.add_argument("--dry-run", action="store_true")
    sync_parser.set_defaults(handler=cmd_sync)

    scan_parser = subparsers.add_parser(
        "scan", help="低 Token 增量检索：同步 Offer 情报局并只输出高匹配新岗位"
    )
    scan_parser.add_argument("--nav", type=int, default=61)
    scan_parser.add_argument("--phase", choices=("提前批", "秋招", "春招"), default="")
    scan_parser.add_argument(
        "--limit", type=int, default=0,
        help="可选截断数量；0 表示输出所有达到阈值的岗位（默认）",
    )
    scan_parser.add_argument("--min-score", type=int, default=35)
    scan_parser.add_argument("--full-sync", action="store_true")
    scan_parser.add_argument("--json", action="store_true")
    scan_parser.set_defaults(handler=cmd_scan)

    exclude_parser = subparsers.add_parser("exclude", help="维护历史岗位排除决策库")
    exclude_subparsers = exclude_parser.add_subparsers(dest="exclude_command", required=True)
    exclude_default = str(
        PROJECT_ROOT / "career" / "求职投递" / "2027届" / "data" / "job_exclusions.yaml"
    )
    exclude_add = exclude_subparsers.add_parser("add", help="加入一条排除规则")
    exclude_add.add_argument("--id", required=True)
    exclude_add.add_argument("--company", default="")
    exclude_add.add_argument("--position-keyword", default="")
    exclude_add.add_argument("--job-id", default="")
    exclude_add.add_argument("--url", default="")
    exclude_add.add_argument("--phase", choices=("", "提前批", "秋招", "春招"), default="")
    exclude_add.add_argument("--reason", required=True)
    exclude_add.add_argument("--expires-at", default="")
    exclude_add.add_argument("--exclusions", default=exclude_default)
    exclude_add.set_defaults(handler=cmd_exclude_add)
    exclude_list = exclude_subparsers.add_parser("list", help="查看生效排除规则")
    exclude_list.add_argument("--phase", choices=("", "提前批", "秋招", "春招"), default="")
    exclude_list.add_argument("--exclusions", default=exclude_default)
    exclude_list.set_defaults(handler=cmd_exclude_list)
    exclude_remove = exclude_subparsers.add_parser("remove", help="停用一条排除规则")
    exclude_remove.add_argument("id")
    exclude_remove.add_argument("--exclusions", default=exclude_default)
    exclude_remove.set_defaults(handler=cmd_exclude_remove)

    shortlist_parser = subparsers.add_parser("shortlist", help="按具身主线评分查看岗位短名单")
    shortlist_parser.add_argument(
        "--phase", choices=("提前批", "秋招", "春招"), default="",
        help="默认读取统一账本的 active_phase",
    )
    shortlist_parser.add_argument("--input", default="", help="指定岗位 JSONL；默认读取 output/ 最新阶段岗位池")
    shortlist_parser.add_argument(
        "--limit", type=int, default=0,
        help="可选截断数量；0 表示输出所有达到阈值的岗位（默认）",
    )
    shortlist_parser.add_argument("--min-score", type=int, default=0)
    shortlist_parser.add_argument("--json", action="store_true")
    shortlist_parser.set_defaults(handler=cmd_shortlist)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args) or 0)
    except (LedgerError, ValueError) as error:
        print(f"[jobctl] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
