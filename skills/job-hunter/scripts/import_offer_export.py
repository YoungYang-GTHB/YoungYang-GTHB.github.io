#!/usr/bin/env python3
"""Import a browser-visible Offer job export into the current recruiting phase pool."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SKILL_ROOT.parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.fetch_jobs import JobFilter, write_jsonl


PHASE_KEYWORDS = {
    "提前批": ("提前批", "提前招聘", "抢先批", "早鸟批", "优招", "先行批"),
    "秋招": ("秋招", "秋季招聘", "秋季校园招聘"),
    "春招": ("春招", "春季招聘", "春季校园招聘"),
}

PHASE_FILE_NAMES = {
    "提前批": "advance",
    "秋招": "autumn",
    "春招": "spring",
}


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"第 {line_number} 行不是有效 JSON: {exc}") from exc
        if isinstance(value, dict):
            records.append(value)
    return records


def detect_phase(record: dict) -> str:
    batch_text = " ".join(
        str(record.get(field, ""))
        for field in ("招聘批次", "招聘阶段", "批次", "职位", "公告标题")
    ).lower()

    # “秋招提前批”应归入提前批，因此提前批的判断必须最先执行。
    for phase in ("提前批", "春招", "秋招"):
        if any(keyword.lower() in batch_text for keyword in PHASE_KEYWORDS[phase]):
            return phase
    return "未知"


def record_identity(record: dict) -> str:
    apply_url = str(record.get("投递地址", "")).strip()
    if apply_url:
        return f"url:{apply_url}"
    return "job:" + "|".join(
        str(record.get(field, "")).strip()
        for field in ("企业名称", "职位", "工作地点")
    )


def build_phase_pool(records: list[dict], phase: str, config: dict) -> list[dict]:
    job_filter = JobFilter(config)
    selected: list[dict] = []
    seen: set[str] = set()

    for raw_record in records:
        if detect_phase(raw_record) != phase:
            continue
        if not job_filter.passes(raw_record):
            continue

        identity = record_identity(raw_record)
        if identity in seen:
            continue
        seen.add(identity)

        record = dict(raw_record)
        record["_stage"] = phase
        record["_match_score"] = job_filter.score(record)
        record["_deadline_status"] = (
            "已记录" if str(record.get("截止时间", "")).strip() else "平台未提供"
        )
        selected.append(record)

    selected.sort(
        key=lambda item: (
            -int(item.get("_match_score", 0)),
            str(item.get("截止时间", "9999-12-31")) or "9999-12-31",
        )
    )
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="导入浏览器同步的 Offer 情报局岗位，并只生成当前招聘阶段候选池"
    )
    parser.add_argument("--input", required=True, help="扩展生成的 raw.jsonl 文件")
    parser.add_argument(
        "--phase",
        choices=tuple(PHASE_KEYWORDS),
        default="提前批",
        help="只保留该阶段岗位（默认：提前批）",
    )
    parser.add_argument("--output", help="输出文件；默认写入项目 output/ 目录")
    parser.add_argument("--dry-run", action="store_true", help="只显示统计，不写文件")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"[import] 文件不存在: {input_path}", file=sys.stderr)
        return 2

    config_path = SKILL_ROOT / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw_records = load_jsonl(input_path)
    phase_records = build_phase_pool(raw_records, args.phase, config)

    print(
        f"[import] 原始 {len(raw_records)} 条 → {args.phase}且符合目标条件 "
        f"{len(phase_records)} 条",
        file=sys.stderr,
    )
    if args.dry_run:
        return 0

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        phase_name = PHASE_FILE_NAMES[args.phase]
        output_path = PROJECT_ROOT / "output" / f"{date_str}-offer-{phase_name}-jobs.jsonl"

    write_jsonl(phase_records, output_path)
    print(f"[import] 已写入: {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
