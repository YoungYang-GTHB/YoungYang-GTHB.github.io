#!/usr/bin/env python3
"""Run the read-only daily recruitment monitoring workflow.

This command combines deadline/opening reminders with the Liepin discovery
scan.  It never edits applications.yaml or monitoring.yaml and never submits
an application.  Browser-dependent discovery may fail independently without
discarding the time-critical reminder report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output/daily-monitor"


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def previous_liepin_snapshot(output_dir: Path, date: str, current: Path) -> tuple[Path | None, dict[str, Any] | None]:
    if current.exists():
        return current, load_json(current)
    candidates = sorted(output_dir.glob("*-liepin-hardtech.json"), reverse=True)
    for candidate in candidates:
        if candidate.name < f"{date}-liepin-hardtech.json":
            payload = load_json(candidate)
            if payload is not None:
                return candidate, payload
    return None, None


def compare_liepin(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    def indexed(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        records = (payload or {}).get("companies", [])
        return {
            str(item.get("liepin_company_id") or item.get("company")): item
            for item in records
            if item.get("liepin_company_id") or item.get("company")
        }

    before = indexed(previous)
    after = indexed(current)
    added = [after[key] for key in sorted(after.keys() - before.keys())]
    removed = [before[key] for key in sorted(before.keys() - after.keys())]
    count_changes = []
    for key in sorted(before.keys() & after.keys()):
        old_count = before[key].get("open_position_count")
        new_count = after[key].get("open_position_count")
        if old_count != new_count:
            count_changes.append(
                {
                    "company": after[key].get("company"),
                    "liepin_company_id": after[key].get("liepin_company_id"),
                    "previous_open_position_count": old_count,
                    "current_open_position_count": new_count,
                }
            )
    return {
        "baseline_available": previous is not None,
        "added_company_count": len(added),
        "removed_company_count": len(removed),
        "position_count_change_count": len(count_changes),
        "added_companies": added,
        "removed_companies": removed,
        "position_count_changes": count_changes,
    }


def run_daily(
    date: str,
    output_dir: Path,
    *,
    cdp: str = "http://127.0.0.1:9222",
    brief_limit: int = 20,
    skip_liepin: bool = False,
) -> tuple[dict[str, Any], int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reminder_results: dict[str, dict[str, Any]] = {}
    for kind in ("apply", "process"):
        result = run_command(
            [
                sys.executable,
                str(SCRIPT_DIR / "jobctl.py"),
                "monitor-due",
                "--date",
                date,
                "--kind",
                kind,
                "--brief",
                "--brief-limit",
                str(brief_limit),
            ]
        )
        kind_path = output_dir / f"{date}-{kind}-reminders.txt"
        kind_path.write_text(result["stdout"] + result["stderr"], encoding="utf-8")
        reminder_results[kind] = {
            "exit_code": result["exit_code"],
            "output": str(kind_path),
            "stderr": result["stderr"],
        }

    # Keep the historic combined file for downstream consumers while making
    # the application and post-application queues independently actionable.
    reminder_path = output_dir / f"{date}-reminders.txt"
    reminder_path.write_text(
        "[applications]\n"
        + Path(reminder_results["apply"]["output"]).read_text(encoding="utf-8")
        + "\n[process]\n"
        + Path(reminder_results["process"]["output"]).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    reminder_exit_code = max(
        reminder_results["apply"]["exit_code"],
        reminder_results["process"]["exit_code"],
    )

    liepin: dict[str, Any] = {
        "skipped": skip_liepin,
        "exit_code": None,
        "output": None,
        "stderr": "",
    }
    if not skip_liepin:
        liepin_path = output_dir / f"{date}-liepin-hardtech.json"
        baseline_path, baseline = previous_liepin_snapshot(output_dir, date, liepin_path)
        # A same-day rerun reads the existing snapshot before the scanner
        # overwrites it. Preserve that exact payload so the emitted delta keeps
        # a reproducible baseline instead of pointing at the new snapshot.
        if baseline is not None and baseline_path == liepin_path:
            baseline_path = output_dir / f"{date}-liepin-baseline.json"
            baseline_path.write_text(
                json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        result = run_command(
            [
                sys.executable,
                str(SCRIPT_DIR / "scan_liepin_hardtech.py"),
                "--cdp",
                cdp,
                "--output",
                str(liepin_path),
            ]
        )
        liepin.update(
            {
                "exit_code": result["exit_code"],
                "output": str(liepin_path) if result["exit_code"] == 0 else None,
                "stderr": result["stderr"],
            }
        )
        if result["exit_code"] == 0:
            current = load_json(liepin_path)
            if current is None:
                try:
                    parsed_stdout = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    parsed_stdout = None
                if isinstance(parsed_stdout, dict):
                    current = parsed_stdout
                    liepin_path.write_text(
                        json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
            if current is None:
                liepin.update({"exit_code": 2, "output": None, "stderr": "scanner output is not valid JSON"})
            else:
                delta = compare_liepin(baseline, current)
                delta["baseline"] = str(baseline_path) if baseline_path else None
                delta_path = output_dir / f"{date}-liepin-delta.json"
                delta_path.write_text(json.dumps(delta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                liepin["delta"] = str(delta_path)

    manifest = {
        "date": date,
        "timezone": "Asia/Shanghai",
        "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "read_only_sources": True,
        "application_submission": False,
        "reminders": {
            "exit_code": reminder_exit_code,
            "output": str(reminder_path),
            "application": reminder_results["apply"],
            "process": reminder_results["process"],
        },
        "liepin_discovery": liepin,
    }
    manifest_path = output_dir / f"{date}-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest"] = str(manifest_path)

    # Deadline reminders are the critical path. Liepin failure is surfaced as
    # a degraded run, while preserving the reminder artifact.
    exit_code = 0
    if reminder_exit_code != 0:
        exit_code = 2
    elif not skip_liepin and liepin["exit_code"] != 0:
        exit_code = 1
    return manifest, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only daily 2027 recruitment monitoring")
    parser.add_argument(
        "--date",
        default=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
        help="Monitoring date in YYYY-MM-DD (default: current Asia/Shanghai date)",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cdp", default="http://127.0.0.1:9222")
    parser.add_argument("--brief-limit", type=int, default=20)
    parser.add_argument("--skip-liepin", action="store_true")
    args = parser.parse_args()

    manifest, exit_code = run_daily(
        args.date,
        args.output_dir,
        cdp=args.cdp,
        brief_limit=args.brief_limit,
        skip_liepin=args.skip_liepin,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
