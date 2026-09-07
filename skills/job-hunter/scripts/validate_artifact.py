#!/usr/bin/env python3
"""Validate job-hunter task and worker-artifact JSON without extra packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit


ROLES = {"discovery", "research", "ranking", "form_prep", "audit"}
ARTIFACT_STATUSES = {"succeeded", "blocked", "failed"}
PHASES = {"", "提前批", "秋招", "春招", "实习", "未知"}
SOURCE_TYPES = {
    "official",
    "official_api",
    "official_candidate_center",
    "official_email",
    "third_party",
    "user_provided",
    "local_snapshot",
}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,255}$")
CN_ID_RE = re.compile(r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)")
MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "cookie",
    "cookies",
    "authorization",
    "access_token",
    "refresh_token",
    "captcha",
    "id_card_number",
    "identity_number",
    "identity_document_number",
}
SENSITIVE_QUERY_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "peopleid",
    "candidateid",
}


class ValidationError(ValueError):
    """Raised when a task or artifact violates its contract."""


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValidationError(f"无法读取 JSON: {source}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"JSON 格式错误: {source}:{error.lineno}: {error.msg}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"JSON 顶层必须是对象: {source}")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def calculate_task_input_digest(document: dict[str, Any]) -> str:
    """Hash the immutable payload and declared input versions."""
    material = {
        "input_refs": document.get("input_refs", []),
        "payload": document.get("payload", {}),
    }
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def validate_task_input_files(
    document: dict[str, Any], *, base_dir: str | Path
) -> list[str]:
    """Verify that every frozen input path still matches its declared hash."""
    errors: list[str] = []
    root = Path(base_dir)
    for index, item in enumerate(document.get("input_refs", []) or []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        source = Path(item["path"]).expanduser()
        if not source.is_absolute():
            source = root / source
        if not source.is_file():
            errors.append(f"task.input_refs[{index}] 文件不存在: {source}")
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            errors.append(f"task.input_refs[{index}] 文件 SHA-256 已变化: {source}")
    return errors


def _require_fields(document: dict[str, Any], fields: set[str], label: str) -> list[str]:
    return [f"{label}.{field} 不能为空" for field in sorted(fields) if field not in document]


def _reject_extra_fields(
    document: dict[str, Any], allowed: set[str], label: str
) -> list[str]:
    return [f"{label} 包含未知字段: {field}" for field in sorted(set(document) - allowed)]


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip().replace("Z", "+00:00")
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        try:
            date.fromisoformat(text[:10])
            return len(text) == 10
        except ValueError:
            return False


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str) or len(value.strip()) <= 10:
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _sensitive_paths(value: Any, prefix: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().casefold().replace("-", "_")
            path = f"{prefix}.{key}"
            if normalized in SENSITIVE_KEYS:
                errors.append(f"禁止在任务/产物中携带敏感字段: {path}")
            errors.extend(_sensitive_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_sensitive_paths(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        if CN_ID_RE.search(value):
            errors.append(f"禁止在任务/产物文本中携带身份证号: {prefix}")
        if MOBILE_RE.search(value):
            errors.append(f"禁止在任务/产物文本中携带手机号: {prefix}")
        if value.lower().startswith(("http://", "https://")):
            try:
                query_keys = {key.casefold() for key, _ in parse_qsl(urlsplit(value).query)}
            except ValueError:
                return errors
            leaked = sorted(query_keys & SENSITIVE_QUERY_KEYS)
            if leaked:
                errors.append(
                    f"URL 必须清除敏感查询参数 {', '.join(leaked)}: {prefix}"
                )
    return errors


def validate_task(document: dict[str, Any]) -> list[str]:
    required = {
        "schema_version",
        "run_id",
        "run_epoch",
        "task_id",
        "role",
        "idempotency_key",
        "input_digest",
        "payload",
    }
    allowed = required | {
        "company_key",
        "phase",
        "priority",
        "max_attempts",
        "created_at",
        "input_refs",
    }
    errors = _require_fields(document, required, "task")
    errors.extend(_reject_extra_fields(document, allowed, "task"))
    if document.get("schema_version") != 1:
        errors.append("task.schema_version 必须为 1")
    for field, limit in (("run_id", 128), ("task_id", 160)):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"task.{field} 必须是 1-{limit} 字符的字符串")
    if document.get("role") not in ROLES:
        errors.append(f"task.role 非法: {document.get('role')}")
    if document.get("phase", "") not in PHASES:
        errors.append(f"task.phase 非法: {document.get('phase')}")
    run_epoch = document.get("run_epoch")
    if isinstance(run_epoch, bool) or not isinstance(run_epoch, int) or run_epoch < 1:
        errors.append("task.run_epoch 必须是大于等于 1 的整数")
    priority = document.get("priority", 100)
    if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 1000:
        errors.append("task.priority 必须是 0-1000 的整数")
    max_attempts = document.get("max_attempts", 3)
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 10:
        errors.append("task.max_attempts 必须是 1-10 的整数")
    key = document.get("idempotency_key")
    if not isinstance(key, str) or not IDEMPOTENCY_RE.fullmatch(key):
        errors.append("task.idempotency_key 格式无效")
    digest = document.get("input_digest")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append("task.input_digest 必须是小写 SHA-256")
    if not isinstance(document.get("payload"), dict):
        errors.append("task.payload 必须是对象")
    elif isinstance(digest, str) and SHA256_RE.fullmatch(digest):
        expected_digest = calculate_task_input_digest(document)
        if digest != expected_digest:
            errors.append("task.input_digest 与 payload/input_refs 不一致")
    created_at = document.get("created_at")
    if created_at is not None and not _valid_datetime(created_at):
        errors.append("task.created_at 必须是 ISO 日期时间")
    input_refs = document.get("input_refs", [])
    if not isinstance(input_refs, list):
        errors.append("task.input_refs 必须是数组")
    else:
        for index, item in enumerate(input_refs):
            if not isinstance(item, dict):
                errors.append(f"task.input_refs[{index}] 必须是对象")
                continue
            if set(item) != {"path", "sha256"}:
                errors.append(f"task.input_refs[{index}] 只能包含 path/sha256")
            if not isinstance(item.get("path"), str) or not item.get("path", "").strip():
                errors.append(f"task.input_refs[{index}].path 不能为空")
            if not isinstance(item.get("sha256"), str) or not SHA256_RE.fullmatch(item.get("sha256", "")):
                errors.append(f"task.input_refs[{index}].sha256 格式无效")
    errors.extend(_sensitive_paths(document))
    return errors


def validate_artifact(document: dict[str, Any]) -> list[str]:
    required = {
        "schema_version",
        "run_id",
        "run_epoch",
        "task_id",
        "role",
        "idempotency_key",
        "input_digest",
        "generated_at",
        "status",
        "facts",
        "evidence",
        "blockers",
        "warnings",
        "next_action",
    }
    errors = _require_fields(document, required, "artifact")
    errors.extend(_reject_extra_fields(document, required, "artifact"))
    if document.get("schema_version") != 1:
        errors.append("artifact.schema_version 必须为 1")
    for field, limit in (("run_id", 128), ("task_id", 160)):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"artifact.{field} 必须是 1-{limit} 字符的字符串")
    role = document.get("role")
    if role not in ROLES:
        errors.append(f"artifact.role 非法: {role}")
    run_epoch = document.get("run_epoch")
    if isinstance(run_epoch, bool) or not isinstance(run_epoch, int) or run_epoch < 1:
        errors.append("artifact.run_epoch 必须是大于等于 1 的整数")
    if document.get("status") not in ARTIFACT_STATUSES:
        errors.append(f"artifact.status 非法: {document.get('status')}")
    key = document.get("idempotency_key")
    if not isinstance(key, str) or not IDEMPOTENCY_RE.fullmatch(key):
        errors.append("artifact.idempotency_key 格式无效")
    digest = document.get("input_digest")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        errors.append("artifact.input_digest 必须是小写 SHA-256")
    if not _valid_datetime(document.get("generated_at")):
        errors.append("artifact.generated_at 必须是 ISO 日期时间")
    facts = document.get("facts")
    if not isinstance(facts, dict):
        errors.append("artifact.facts 必须是对象")
        facts = {}
    role_requirements = {
        "discovery": {"leads"},
        "research": {"pool_scan", "jobs"},
        "ranking": {"ranking", "recommendation"},
        "form_prep": {"form_snapshot", "missing_fields", "resume"},
        "audit": {"decision", "checks"},
    }
    if document.get("status") == "succeeded":
        for field in role_requirements.get(str(role), set()):
            if field not in facts:
                errors.append(f"artifact.facts.{field} 是 {role} 成功产物的必填字段")
        expected_fact_types = {
            "discovery": {"leads": list},
            "research": {"pool_scan": dict, "jobs": list},
            "ranking": {"ranking": list, "recommendation": dict},
            "form_prep": {"form_snapshot": dict, "missing_fields": list, "resume": dict},
            "audit": {"checks": list},
        }
        for field, expected_type in expected_fact_types.get(str(role), {}).items():
            if field in facts and not isinstance(facts[field], expected_type):
                errors.append(
                    f"artifact.facts.{field} 必须是 {expected_type.__name__}"
                )
    if role == "audit" and document.get("status") == "succeeded" and facts.get("decision") not in {
        "pass",
        "blocked",
        "needs_user_action",
    }:
        errors.append("artifact.facts.decision 必须是 pass/blocked/needs_user_action")
    if role == "ranking" and document.get("status") == "succeeded":
        score_fields = {
            "experience_fit",
            "deployment_fit",
            "research_fit",
            "location_fit",
            "quota_risk",
            "phase_risk",
            "evidence_quality",
        }
        ranks = facts.get("ranking", [])
        seen_ranks: set[int] = set()
        recommended_job_key = str((facts.get("recommendation") or {}).get("job_key") or "")
        for index, item in enumerate(ranks if isinstance(ranks, list) else []):
            prefix = f"artifact.facts.ranking[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            required_row = {
                "rank",
                "job_key",
                "hard_gate",
                "overall_score",
                "scores",
                "matching_evidence",
                "capability_gaps",
                "exclusion_reason",
            }
            errors.extend(_require_fields(item, required_row, prefix))
            rank = item.get("rank")
            if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
                errors.append(f"{prefix}.rank 必须是正整数")
            elif rank in seen_ranks:
                errors.append(f"{prefix}.rank 不能重复")
            else:
                seen_ranks.add(rank)
            gate = item.get("hard_gate")
            if gate not in {"pass", "conditional", "fail"}:
                errors.append(f"{prefix}.hard_gate 非法")
            if gate == "fail" and item.get("job_key") == recommended_job_key:
                errors.append(f"{prefix} 硬门槛失败岗位不能成为推荐项")
            scores = item.get("scores")
            if not isinstance(scores, dict) or set(scores) != score_fields:
                errors.append(f"{prefix}.scores 必须包含固定七个评分维度")
            else:
                for field, value in scores.items():
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
                        errors.append(f"{prefix}.scores.{field} 必须在 0-100")
            overall = item.get("overall_score")
            if isinstance(overall, bool) or not isinstance(overall, (int, float)) or not 0 <= overall <= 100:
                errors.append(f"{prefix}.overall_score 必须在 0-100")
            for field in ("matching_evidence", "capability_gaps"):
                value = item.get(field)
                if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
                    errors.append(f"{prefix}.{field} 必须是字符串数组")
        recommendation = facts.get("recommendation")
        if not isinstance(recommendation, dict) or not recommended_job_key:
            errors.append("artifact.facts.recommendation.job_key 不能为空")
        elif not isinstance(recommendation.get("reason"), str) or not recommendation["reason"].strip():
            errors.append("artifact.facts.recommendation.reason 不能为空")
    for field in ("blockers", "warnings"):
        value = document.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"artifact.{field} 必须是字符串数组")
    if not isinstance(document.get("next_action"), str):
        errors.append("artifact.next_action 必须是字符串")
    evidence = document.get("evidence")
    if not isinstance(evidence, list):
        errors.append("artifact.evidence 必须是数组")
        evidence = []
    for index, item in enumerate(evidence):
        prefix = f"artifact.evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} 必须是对象")
            continue
        allowed = {"field", "url", "source_type", "observed_at", "summary", "content_sha256"}
        errors.extend(_require_fields(item, {"field", "url", "source_type", "observed_at", "summary"}, prefix))
        errors.extend(_reject_extra_fields(item, allowed, prefix))
        if item.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{prefix}.source_type 非法")
        if not _valid_timestamp(item.get("observed_at")):
            errors.append(f"{prefix}.observed_at 必须是 ISO 日期或日期时间")
        if not isinstance(item.get("summary"), str) or not item.get("summary", "").strip():
            errors.append(f"{prefix}.summary 不能为空")
        if not isinstance(item.get("url"), str):
            errors.append(f"{prefix}.url 必须是字符串")
        digest_value = item.get("content_sha256")
        if digest_value is not None and (
            not isinstance(digest_value, str) or not SHA256_RE.fullmatch(digest_value)
        ):
            errors.append(f"{prefix}.content_sha256 格式无效")
    if role == "research" and document.get("status") == "succeeded":
        official = {"official", "official_api", "official_candidate_center", "official_email"}
        if not any(item.get("source_type") in official for item in evidence if isinstance(item, dict)):
            errors.append("成功的 research 产物至少需要一条官方证据")
        pool = facts.get("pool_scan")
        required_pool = {
            "official_entry",
            "scanned_at",
            "total_jobs",
            "pages_or_query_scope",
            "complete",
            "graduation_year_verified",
            "full_time_verified",
        }
        if not isinstance(pool, dict):
            errors.append("artifact.facts.pool_scan 必须是对象")
        else:
            errors.extend(_require_fields(pool, required_pool, "artifact.facts.pool_scan"))
            if pool.get("complete") is not True:
                errors.append("artifact.facts.pool_scan.complete 必须为 true")
            for field in ("graduation_year_verified", "full_time_verified"):
                if pool.get(field) is not True:
                    errors.append(f"artifact.facts.pool_scan.{field} 必须为 true")
            for field in ("official_entry", "pages_or_query_scope"):
                if not isinstance(pool.get(field), str) or not pool[field].strip():
                    errors.append(f"artifact.facts.pool_scan.{field} 不能为空")
            total_jobs = pool.get("total_jobs")
            if isinstance(total_jobs, bool) or not isinstance(total_jobs, int) or total_jobs < 0:
                errors.append("artifact.facts.pool_scan.total_jobs 必须是非负整数")
            elif isinstance(facts.get("jobs"), list) and total_jobs != len(facts["jobs"]):
                errors.append("artifact.facts.pool_scan.total_jobs 必须与 jobs 数量一致")
            if not _valid_timestamp(pool.get("scanned_at")):
                errors.append("artifact.facts.pool_scan.scanned_at 必须是 ISO 日期或日期时间")
    if role == "form_prep" and document.get("status") == "succeeded":
        snapshot = facts.get("form_snapshot")
        required_snapshot = {
            "company_key",
            "job_id",
            "title",
            "page_url",
            "filled_fields",
            "validation_errors",
        }
        if not isinstance(snapshot, dict):
            errors.append("artifact.facts.form_snapshot 必须是对象")
        else:
            errors.extend(
                _require_fields(snapshot, required_snapshot, "artifact.facts.form_snapshot")
            )
            for field in ("company_key", "job_id", "title", "page_url"):
                if not isinstance(snapshot.get(field), str) or not snapshot[field].strip():
                    errors.append(f"artifact.facts.form_snapshot.{field} 不能为空")
            for field in ("filled_fields", "validation_errors"):
                value = snapshot.get(field)
                if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
                    errors.append(f"artifact.facts.form_snapshot.{field} 必须是字符串数组")
        resume = facts.get("resume")
        if not isinstance(resume, dict):
            errors.append("artifact.facts.resume 必须是对象")
        else:
            errors.extend(_require_fields(resume, {"filename", "sha256"}, "artifact.facts.resume"))
            if not isinstance(resume.get("filename"), str) or not resume["filename"].strip():
                errors.append("artifact.facts.resume.filename 不能为空")
            if not isinstance(resume.get("sha256"), str) or not SHA256_RE.fullmatch(resume.get("sha256", "")):
                errors.append("artifact.facts.resume.sha256 格式无效")
    errors.extend(_sensitive_paths(document))
    return errors


def assert_valid_artifact(
    artifact: dict[str, Any], task: dict[str, Any] | None = None
) -> None:
    errors = validate_artifact(artifact)
    if task is not None:
        task_errors = validate_task(task)
        errors.extend(f"关联任务无效: {item}" for item in task_errors)
        for field in (
            "run_id",
            "run_epoch",
            "task_id",
            "role",
            "idempotency_key",
            "input_digest",
        ):
            if artifact.get(field) != task.get(field):
                errors.append(f"artifact.{field} 与任务不一致")
    if errors:
        raise ValidationError("产物校验失败:\n- " + "\n- ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="worker artifact JSON")
    parser.add_argument("--task", default="", help="可选的关联 task JSON")
    args = parser.parse_args()
    try:
        artifact = load_json_object(args.artifact)
        task = load_json_object(args.task) if args.task else None
        if task is not None:
            file_errors = validate_task_input_files(task, base_dir=Path(args.task).parent)
            if file_errors:
                raise ValidationError("关联任务输入校验失败:\n- " + "\n- ".join(file_errors))
        assert_valid_artifact(artifact, task)
    except ValidationError as error:
        print(f"[validate-artifact] {error}", file=sys.stderr)
        return 2
    print(f"[validate-artifact] 校验通过: {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
