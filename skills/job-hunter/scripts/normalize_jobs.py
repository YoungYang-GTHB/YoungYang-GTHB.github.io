#!/usr/bin/env python3
"""Normalize user-provided job posts into jobs.jsonl."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from typing import Iterable


FIELD_ALIASES = {
    "platform": ["platform", "平台", "来源"],
    "company": ["company", "公司", "企业"],
    "title": ["title", "岗位", "职位", "job_title", "position"],
    "city": ["city", "城市", "地点", "工作地"],
    "url": ["url", "链接", "岗位链接"],
    "jd_text": ["jd_text", "JD", "职责", "岗位描述", "描述", "要求"],
    "hard_requirements": ["hard_requirements", "硬性要求"],
    "nice_to_have": ["nice_to_have", "加分项"],
    "user_interest": ["user_interest", "兴趣", "意向"],
}


def first_value(row: dict[str, str], field: str) -> str:
    for key in FIELD_ALIASES[field]:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def make_id(record: dict[str, str]) -> str:
    raw = "|".join(record.get(k, "") for k in ["platform", "company", "title", "city", "url", "jd_text"])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def normalize_row(row: dict[str, str], source_type: str, observed_at: str, default_platform: str) -> dict[str, str]:
    record = {
        "platform": first_value(row, "platform") or default_platform,
        "company": first_value(row, "company"),
        "title": first_value(row, "title"),
        "city": first_value(row, "city"),
        "url": first_value(row, "url"),
        "observed_at": observed_at,
        "source_type": source_type,
        "jd_text": first_value(row, "jd_text"),
        "hard_requirements": first_value(row, "hard_requirements"),
        "nice_to_have": first_value(row, "nice_to_have"),
        "user_interest": first_value(row, "user_interest"),
    }
    record["job_id"] = make_id(record)
    return record


def parse_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def parse_text_blocks(text: str) -> list[dict[str, str]]:
    blocks = [b.strip() for b in re.split(r"\n\s*(?:---|### .+)\s*\n", text) if b.strip()]
    rows: list[dict[str, str]] = []
    for block in blocks:
        row: dict[str, str] = {"jd_text": block}
        for label, field in [("平台", "platform"), ("公司", "company"), ("岗位", "title"), ("职位", "title"), ("城市", "city"), ("链接", "url")]:
            match = re.search(rf"{label}\s*[:：]\s*(.+)", block)
            if match:
                row[field] = match.group(1).strip()
        rows.append(row)
    return rows


def load_rows(path: pathlib.Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_csv(path)
    text = path.read_text(encoding="utf-8")
    table_rows = parse_markdown_table(text)
    if table_rows:
        return table_rows
    return parse_text_blocks(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="CSV, Markdown table, or text file")
    parser.add_argument("--output", required=True, help="Output jobs.jsonl path")
    parser.add_argument("--source-type", default="user_paste", help="user_paste|screenshot|csv_export|browser_visible|manual_entry")
    parser.add_argument("--platform", default="", help="Default platform when input lacks one")
    parser.add_argument("--observed-at", default=dt.date.today().isoformat())
    args = parser.parse_args()

    input_path = pathlib.Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    rows = load_rows(input_path)
    records = [
        normalize_row(row, args.source_type, args.observed_at, args.platform)
        for row in rows
        if any(str(value).strip() for value in row.values())
    ]

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} jobs to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
