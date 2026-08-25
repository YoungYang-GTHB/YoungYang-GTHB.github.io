#!/usr/bin/env python3
"""Scan Liepin's hard-tech topic as a discovery source.

The topic mixes social, internship and campus jobs.  This scanner therefore
only emits company leads and never promotes a company to a 2027 application.
It uses an already running Chrome CDP session because the page is rendered by
client-side JavaScript.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

try:
    import websocket
except ImportError:  # pragma: no cover - exercised through CLI error path
    websocket = None


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOPIC = "https://wow.liepin.com/t1016359/37d6a562.html"
DEFAULT_CDP = "http://127.0.0.1:9222"

ALIASES = {
    "宇树科技unitree": ("宇树科技",),
    "北京银河通用机器人有限公司": ("银河通用",),
    "自变量机器人科技深圳有限公司": ("自变量机器人",),
    "北京星动纪元科技有限公司": ("星动纪元",),
    "智平方深圳科技股份有限公司": ("智平方", "ai2robotics"),
    "智平方具身科技深圳有限公司": ("智平方", "ai2robotics"),
    "北京极佳视界科技有限公司": ("极佳视界", "极佳科技"),
    "北京人形机器人创新中心有限公司": ("北京人形机器人创新中心",),
    "北京格拉飞可斯科技有限公司": ("太极图形", "meshyai"),
}

MATCH_KEYWORDS = (
    "具身智能", "具身", "世界模型", "基础模型", "大模型", "多模态",
    "vla", "机器人", "ai", "人工智能", "模型训练", "推理", "编译器",
    "高性能计算", "数据闭环", "仿真",
)


def normalize_company(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[（(].*?[）)]", "", value)
    value = re.sub(
        r"有限责任公司|股份有限公司|有限公司|科技|机器人|智能|集团|中国|北京|上海|深圳|杭州",
        "",
        value,
    )
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def parse_card(card: dict[str, Any]) -> dict[str, Any]:
    lines = [str(line).strip() for line in card.get("text", "").splitlines() if str(line).strip()]
    if not lines:
        raise ValueError("empty company card")
    count_match = re.search(r"(\d+)个在招职位", "\n".join(lines))
    return {
        "company": lines[0],
        "liepin_company_id": str(card.get("company_id", "")),
        "summary": " ".join(lines[1:-1]) if len(lines) > 2 else "",
        "open_position_count": int(count_match.group(1)) if count_match else None,
    }


def load_known_companies(root: Path = PROJECT_ROOT) -> list[str]:
    data_dir = root / "career/求职投递/2027届/data"
    companies: list[str] = []
    for filename in ("applications.yaml", "monitoring.yaml"):
        payload = yaml.safe_load((data_dir / filename).read_text(encoding="utf-8"))
        records = (
            payload
            if isinstance(payload, list)
            else payload.get("applications", payload.get("monitors", payload.get("items", [])))
        )
        for record in records or []:
            company = str(record.get("company", "")).strip()
            if company:
                companies.append(company)
    return companies


def is_known_company(company: str, known_companies: list[str]) -> tuple[bool, str]:
    compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", company.casefold())
    candidates = [company, *ALIASES.get(compact, ())]
    for known in known_companies:
        known_compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", known.casefold())
        known_norm = normalize_company(known)
        for candidate in candidates:
            candidate_compact = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", candidate.casefold())
            candidate_norm = normalize_company(candidate)
            if candidate_compact and (
                candidate_compact in known_compact or known_compact in candidate_compact
            ):
                return True, known
            if len(candidate_norm) >= 2 and len(known_norm) >= 2 and (
                candidate_norm in known_norm or known_norm in candidate_norm
            ):
                return True, known
    return False, ""


def rank_lead(record: dict[str, Any]) -> dict[str, Any]:
    corpus = f"{record['company']} {record['summary']}".casefold()
    hits = [keyword for keyword in MATCH_KEYWORDS if keyword.casefold() in corpus]
    record["match_keywords"] = hits
    record["lead_score"] = min(100, len(hits) * 10)
    record["evidence_level"] = "discovery_only"
    record["requires_official_2027_verification"] = True
    return record


class CDPClient:
    def __init__(self, websocket_url: str):
        if websocket is None:
            raise RuntimeError("missing websocket-client; install requirements-optional.txt")
        self.ws = websocket.create_connection(websocket_url, timeout=20, suppress_origin=True)
        self.sequence = 0

    def close(self) -> None:
        self.ws.close()

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.sequence += 1
        call_id = self.sequence
        self.ws.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == call_id:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message

    def evaluate(self, expression: str) -> Any:
        result = self.command(
            "Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True}
        )
        remote = result.get("result", {}).get("result", {})
        if remote.get("subtype") == "error":
            raise RuntimeError(str(remote.get("description", "browser evaluation failed")))
        return remote.get("value")


def open_target(cdp: str, topic_url: str) -> CDPClient:
    request = Request(f"{cdp.rstrip('/')}/json/new?{quote(topic_url, safe=':/?=&')}", method="PUT")
    with urlopen(request, timeout=10) as response:
        target = json.load(response)
    return CDPClient(target["webSocketDebuggerUrl"])


def scan_topic(cdp: str, topic_url: str, wait_seconds: float = 2.0) -> list[dict[str, Any]]:
    client = open_target(cdp, topic_url)
    records: dict[str, dict[str, Any]] = {}
    try:
        client.command("Page.enable")
        deadline = time.time() + 20
        while time.time() < deadline:
            if client.evaluate("document.querySelectorAll('.searchcompanys-company-card').length"):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Liepin topic did not render company cards within 20 seconds")

        # Cards appear before the pagination finishes its entrance animation.
        # Reading page numbers immediately can therefore truncate the last page.
        time.sleep(wait_seconds)
        page_count = int(
            client.evaluate(
                "Math.max(...[...document.querySelectorAll('.ant-pagination-item')].map(e=>Number(e.title)||0))"
            )
            or 1
        )
        page = 1
        previous_signature = ""
        while page <= page_count:
            if page > 1:
                clicked = client.evaluate(
                    f"Boolean(document.querySelector('.ant-pagination-item-{page}') && "
                    f"(document.querySelector('.ant-pagination-item-{page}').click() || true))"
                )
                if not clicked:
                    raise RuntimeError(f"could not open topic page {page}")
                switch_deadline = time.time() + 10
                while time.time() < switch_deadline:
                    active_page = client.evaluate(
                        "document.querySelector('.ant-pagination-item-active')?.title || ''"
                    )
                    current_signature = client.evaluate(
                        "JSON.stringify([...document.querySelectorAll('.searchcompanys-company-card')]"
                        ".map(card => card.dataset.tlgScm || card.innerText.split('\\n')[0]))"
                    )
                    if str(active_page) == str(page) and current_signature != previous_signature:
                        break
                    time.sleep(0.2)
                else:
                    raise RuntimeError(f"topic page {page} did not render new company cards")
                time.sleep(wait_seconds)
            cards = client.evaluate(
                """
                [...document.querySelectorAll('.searchcompanys-company-card')].map(card => ({
                  text: card.innerText,
                  company_id: (card.dataset.tlgScm || '').match(/cid=(\\d+)/)?.[1] || ''
                }))
                """
            )
            for raw in cards or []:
                parsed = parse_card(raw)
                key = parsed["liepin_company_id"] or parsed["company"]
                records[key] = parsed
            previous_signature = json.dumps(
                [raw.get("company_id") or str(raw.get("text", "")).splitlines()[0] for raw in cards or []],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            page_count = max(
                page_count,
                int(
                    client.evaluate(
                        "Math.max(...[...document.querySelectorAll('.ant-pagination-item')].map(e=>Number(e.title)||0))"
                    )
                    or page_count
                ),
            )
            page += 1
    finally:
        client.close()
    return list(records.values())


def build_report(records: list[dict[str, Any]], known_companies: list[str]) -> dict[str, Any]:
    leads = []
    for record in records:
        known, matched = is_known_company(record["company"], known_companies)
        record["known_in_ledger"] = known
        record["matched_ledger_company"] = matched
        leads.append(rank_lead(record))
    leads.sort(key=lambda item: (item["known_in_ledger"], -item["lead_score"], item["company"]))
    return {
        "source": DEFAULT_TOPIC,
        "source_type": "third_party_company_discovery",
        "warning": "Position counts mix social, internship and campus jobs; verify official 2027 full-time evidence.",
        "company_count": len(leads),
        "new_company_count": sum(not item["known_in_ledger"] for item in leads),
        "companies": leads,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Liepin hard-tech topic through an existing Chrome CDP session")
    parser.add_argument("--cdp", default=DEFAULT_CDP)
    parser.add_argument("--url", default=DEFAULT_TOPIC)
    parser.add_argument("--wait-seconds", type=float, default=2.0)
    parser.add_argument("--output", type=Path, help="Optional JSON output; stdout is always printed")
    args = parser.parse_args()

    try:
        records = scan_topic(args.cdp, args.url, args.wait_seconds)
        report = build_report(records, load_known_companies())
    except Exception as exc:
        print(f"[liepin-hardtech] scan failed: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
