#!/usr/bin/env python3
"""Build conservative company and logical-job keys for duplicate prevention."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml


DROP_QUERY_KEYS = {
    "access_token",
    "candidateid",
    "from",
    "peopleid",
    "recommendcode",
    "referral",
    "referralcode",
    "refresh_token",
    "shareid",
    "sharesource",
    "source",
    "token",
    "track",
    "tracking",
}


def normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"[\s\-_.·•—–/\\()（）\[\]【】]+", "", text)


def load_company_aliases(path: str | Path | None) -> dict[str, str]:
    if not path:
        return {}
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("company alias file schema_version must be 1")
    companies = payload.get("companies", []) if isinstance(payload, dict) else []
    if not isinstance(companies, list):
        raise ValueError("company alias file must contain a companies list")
    aliases: dict[str, str] = {}
    for item in companies:
        if not isinstance(item, dict):
            raise ValueError("each company alias entry must be an object")
        company_id = str(item.get("id", "")).strip()
        canonical_name = str(item.get("canonical_name", "")).strip()
        if not company_id or not canonical_name:
            raise ValueError("company alias entry requires id and canonical_name")
        for name in [canonical_name, *(item.get("aliases", []) or [])]:
            normalized = normalized_text(name)
            if normalized in aliases and aliases[normalized] != company_id:
                raise ValueError(f"company alias collision: {name}")
            aliases[normalized] = company_id
    return aliases


def canonical_company_key(company: str, aliases: dict[str, str] | None = None) -> str:
    normalized = normalized_text(company)
    if not normalized:
        raise ValueError("company cannot be empty")
    mapped = (aliases or {}).get(normalized)
    if mapped:
        return mapped
    # Keep unknown names conservative: normalize formatting but do not strip
    # legal suffixes, which could merge distinct recruiting entities.
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"company-{digest}"


def _keep_query_pair(key: str) -> bool:
    lowered = key.casefold()
    return lowered not in DROP_QUERY_KEYS and not lowered.startswith("utm_")


def canonical_url(value: str) -> str:
    parsed = urlsplit(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parsed.query) if _keep_query_pair(k)))
    fragment = parsed.fragment
    if "?" in fragment:
        fragment_path, fragment_query = fragment.split("?", 1)
        clean_fragment_query = urlencode(
            sorted((k, v) for k, v in parse_qsl(fragment_query) if _keep_query_pair(k))
        )
        fragment = fragment_path + (f"?{clean_fragment_query}" if clean_fragment_query else "")
    elif any(key in fragment.casefold() for key in ("access_token=", "token=", "peopleid=")):
        fragment = ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), path, query, fragment))


def logical_job_key(
    *,
    company_key: str,
    program: str,
    phase: str,
    official_job_id: str = "",
    official_url: str = "",
    title: str = "",
    locations: list[str] | None = None,
) -> str:
    if official_job_id.strip():
        identity = [company_key, normalized_text(program), normalized_text(phase), "id", official_job_id.strip()]
    elif canonical_url(official_url):
        identity = [company_key, normalized_text(program), normalized_text(phase), "url", canonical_url(official_url)]
    else:
        normalized_locations = sorted(normalized_text(item) for item in (locations or []) if normalized_text(item))
        if not normalized_text(title):
            raise ValueError("title is required when no official job id or URL exists")
        identity = [
            company_key,
            normalized_text(program),
            normalized_text(phase),
            "fallback",
            normalized_text(title),
            *normalized_locations,
        ]
    digest = hashlib.sha256(json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"job-{digest}"


def job_version(
    *,
    job_key: str,
    jd: dict[str, Any],
    status: str,
    locations: list[str] | None = None,
    updated_at: str = "",
) -> str:
    """Fingerprint the official fields whose change requires re-evaluation."""

    key = str(job_key or "").strip()
    if not key:
        raise ValueError("job_key cannot be empty")
    if not isinstance(jd, dict):
        raise ValueError("jd must be an object")
    payload = {
        "job_key": key,
        "jd": jd,
        "locations": sorted(
            normalized_text(item) for item in (locations or []) if normalized_text(item)
        ),
        "status": normalized_text(status),
        "updated_at": str(updated_at or "").strip(),
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"job-version-{digest}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", required=True)
    parser.add_argument("--program", default="")
    parser.add_argument("--phase", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--location", action="append", default=[])
    parser.add_argument("--aliases")
    args = parser.parse_args()
    aliases = load_company_aliases(args.aliases)
    company_key = canonical_company_key(args.company, aliases)
    print(
        json.dumps(
            {
                "company_key": company_key,
                "canonical_url": canonical_url(args.url),
                "job_key": logical_job_key(
                    company_key=company_key,
                    program=args.program,
                    phase=args.phase,
                    official_job_id=args.job_id,
                    official_url=args.url,
                    title=args.title,
                    locations=args.location,
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
