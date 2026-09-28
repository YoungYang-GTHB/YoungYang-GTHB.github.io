"""Company-level discovery, not eligibility or permission to apply.

Build from every fetched row *before* incremental/job/URL filters. A feed's
missing target keyword (or an unsuitable advertised job) says nothing about
the company's complete official campus pool.
"""

from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone

from scripts.exclusions import normalize_text


def _lead_url(value):
    """Keep a research entry, never credentials, referral codes or query tokens."""
    try:
        parts = urlsplit(str(value or ""))
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return ""
        if parts.username or parts.password:
            return ""
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except ValueError:
        return ""


def build_company_review_queue(records, job_filter, exclusions, recent_companies=()):
    """Return one exact-name lead per company, including explicit held states.

    Company-only exclusion rules remain hard holds. A job-specific exclusion
    stays attached to that lead, without claiming every job at the employer is
    ineligible. Feed cohort/location/industry values remain unverified hints.
    No canonical ledger, official eligibility or application state is changed.
    """
    grouped = {}
    for record in records:
        company = str(record.get("企业名称") or "").strip()
        key = normalize_text(company)
        if key:
            grouped.setdefault(key, []).append(record)
    if not grouped:
        return []
    phase = job_filter._phase or ""
    rules = exclusions.active_rules(phase)
    recent = {normalize_text(name) for name in recent_companies}
    result = []
    for key, rows in grouped.items():
        company_rules = [
            rule for rule in rules
            if normalize_text(rule.get("company"))
            and normalize_text(rule.get("company")) in key
            and not any(rule.get(field) for field in ("position_keyword", "job_id", "url"))
        ]
        job_rule_ids = set()
        reasons, urls, titles = set(), set(), set()
        scores = []
        for row in rows:
            scored = dict(row)  # scoring annotates its input; do not mutate the feed
            scores.append(job_filter.score(scored))
            reasons.update(scored.get("_match_reasons", []))
            title = str(row.get("职位") or row.get("招聘公告") or "").strip()
            if title:
                titles.add(title)
            for field in ("投递地址", "公告链接"):
                url = _lead_url(row.get(field))
                if url:
                    urls.add(url)
            rule = exclusions.match(row, phase=phase)
            if rule and rule not in company_rules:
                job_rule_ids.add(str(rule.get("id", "")))
        status = "pending_official_review"
        if company_rules:
            status = "held_company_exclusion"
        elif key in recent:
            status = "held_history_review"
        result.append({
            "company": rows[0]["企业名称"],
            "company_key_candidate": key,
            "company_identity_verified": False,
            "identity_sources": sorted({str(row.get("_company_identity_source") or "feed_unverified") for row in rows}),
            "review_status": status,
            "priority_score": max(scores, default=0),
            "keyword_reasons": sorted(reasons),
            "recall_channel": "company_official_pool_review",
            "source_row_count": len(rows),
            "source_titles": sorted(titles),
            "lead_urls": sorted(urls),
            "lead_url_semantics": "sanitized_company_discovery_only_not_exact_job_evidence",
            "company_exclusion_ids": sorted(str(rule.get("id", "")) for rule in company_rules),
            "excluded_job_rule_ids": sorted(job_rule_ids),
            "source_hints": {
                field: sorted({str(row.get(field) or "") for row in rows} - {""})
                for field in ("毕业年份", "工作地点", "学历要求", "行业")
            },
            "official_pool_verified": False,
            "eligibility": "unknown",
            "history_check_required": True,
            "application_authorized": False,
            "next_action": "review_exclusion_or_history" if status.startswith("held_") else "verify_complete_official_campus_pool",
        })
    return sorted(result, key=lambda row: (-row["priority_score"], row["company_key_candidate"]))


def merge_company_review_queue(previous, current, exclusions, phase="", observed_at=None):
    """Persist discovery across incremental runs; absence is not closure.

    Retain each navigation + exact company identity independently. Reapply
    company-level holds using today's exclusions even when a company was not
    fetched this run. Exact job eligibility/exclusions still need official review.
    """
    now = observed_at or datetime.now(timezone.utc).isoformat()
    key = lambda row: (str(row.get("source_navigation_id", "")), row["company_key_candidate"])
    merged = {key(row): dict(row, seen_in_current_fetch=False) for row in previous}
    for row in current:
        old = merged.get(key(row), {})
        item = dict(row, seen_in_current_fetch=True, last_seen_at=now,
                    first_seen_at=old.get("first_seen_at", now))
        for field in ("source_titles", "lead_urls", "identity_sources"):
            item[field] = sorted(set(old.get(field, [])) | set(row.get(field, [])))
        merged[key(row)] = item
    rules = exclusions.active_rules(phase)
    for item in merged.values():
        company_rules = [rule for rule in rules
                         if normalize_text(rule.get("company"))
                         and normalize_text(rule.get("company")) in item["company_key_candidate"]
                         and not any(rule.get(f) for f in ("position_keyword", "job_id", "url"))]
        item["company_exclusion_ids"] = sorted(str(rule.get("id", "")) for rule in company_rules)
        if company_rules:
            item["review_status"] = "held_company_exclusion"
        elif item.get("review_status") == "held_company_exclusion":
            item["review_status"] = "pending_official_review"
        item["next_action"] = ("review_exclusion_or_history" if item["review_status"].startswith("held_")
                               else "verify_complete_official_campus_pool")
        item["exclusions_checked_at"] = now
        item["job_exclusions_check_required"] = True
        item["history_check_required"] = True
        item["application_authorized"] = False
    return sorted(merged.values(), key=lambda row: (-row["priority_score"], key(row)))
