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
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = (
    PROJECT_ROOT / "career" / "求职投递" / "2027届" / "data" / "applications.yaml"
)
DEFAULT_SUMMARY = PROJECT_ROOT / "career" / "求职投递" / "2027届" / "投递汇总.md"

sys.path.insert(0, str(SKILL_ROOT))

from scripts.state import FetcherState
from scripts.tracker import ApplicationTracker


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


class LedgerError(ValueError):
    pass


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
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
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
            if item.get("status") in {"applied", "screening", "interview", "offer"}:
                for field in ("applied_at", "channel", "resume"):
                    if not stringify(item.get(field)).strip():
                        errors.append(f"{prefix}.{field} 在已投递状态下不能为空")
            resume = stringify(item.get("resume"))
            if resume and not (PROJECT_ROOT / resume).exists():
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
    print(f"[jobctl] 账本校验通过：{len(ledger.applications)} 条")
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


def print_preflight(application: dict[str, Any]) -> None:
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
    print(f"确认令牌: {confirmation_token(application)}")
    print("说明: 此令牌只用于记录本人已确认；验证码和招聘网站最终提交仍由浏览器流程处理。")


def ensure_submittable(ledger: ApplicationLedger, application: dict[str, Any]) -> None:
    active_phase = ledger.data.get("active_phase")
    if application.get("phase") != active_phase:
        raise LedgerError(
            f"当前只投 {active_phase}，该岗位属于 {application.get('phase')}，已阻止进入提交流程"
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
    print_preflight(application)
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
    selected = records[: args.limit]
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0
    print(f"岗位池: {input_path}；共 {len(records)} 条；显示前 {len(selected)} 条")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="统一投递账本路径")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="查看统一投递统计")
    status_parser.set_defaults(handler=cmd_status)

    validate_parser = subparsers.add_parser("validate", help="校验账本和简历文件")
    validate_parser.set_defaults(handler=cmd_validate)

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

    shortlist_parser = subparsers.add_parser("shortlist", help="按具身主线评分查看岗位短名单")
    shortlist_parser.add_argument(
        "--phase", choices=("提前批", "秋招", "春招"), default="",
        help="默认读取统一账本的 active_phase",
    )
    shortlist_parser.add_argument("--input", default="", help="指定岗位 JSONL；默认读取 output/ 最新阶段岗位池")
    shortlist_parser.add_argument("--limit", type=int, default=20)
    shortlist_parser.add_argument("--json", action="store_true")
    shortlist_parser.set_defaults(handler=cmd_shortlist)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args) or 0)
    except LedgerError as error:
        print(f"[jobctl] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
