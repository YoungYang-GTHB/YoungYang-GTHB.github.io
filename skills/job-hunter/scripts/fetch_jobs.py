#!/usr/bin/env python3
"""
fetch_jobs — 从 offer情报局 增量拉取校招岗位。

用法:
  python3 fetch_jobs.py                    # 增量模式（默认，仅抓更新）
  python3 fetch_jobs.py --full-sync        # 全量模式（每周自动触发）
  python3 fetch_jobs.py --list-navigations # 列出可用数据源
  python3 fetch_jobs.py --dry-run          # 预览，不写入文件
  python3 fetch_jobs.py --nav 61           # 只拉取指定导航
  python3 fetch_jobs.py --phase 提前批      # 只保留当前招聘阶段
  python3 fetch_jobs.py --wechat-login     # 纯终端微信扫码登录
  python3 fetch_jobs.py --save-token <TK>  # 保存 token
  python3 fetch_jobs.py --check-token      # 检查 token 状态
  python3 fetch_jobs.py --stats            # 查看抓取状态摘要

提效策略:
  1. 增量模式: 每页先检查最新 更新时间，遇到 <=上次最新时间的记录即停止
  2. 异常检测: 总数变化 ≥15% 自动升级为全量
  3. 兜底机制: 每 7 天自动全量同步一次
  4. 已投递/忽略的公司30天内跳过展示（不重复提醒）
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(SKILL_ROOT))

from scripts.auth import TokenManager
from scripts.api import OfferAPI
from scripts.exclusions import ExclusionStore
from scripts.state import FetcherState
from scripts.tracker import ApplicationTracker


PHASE_KEYWORDS = {
    "提前批": ("提前批", "提前招聘", "抢先批", "早鸟批", "优招", "先行批"),
    "秋招": ("秋招", "秋季招聘", "秋季校园招聘"),
    "春招": ("春招", "春季招聘", "春季校园招聘"),
}


def detect_phase(record: dict) -> str:
    batch_text = " ".join(
        str(record.get(field, ""))
        for field in ("招聘批次", "招聘阶段", "批次", "职位", "公告标题")
    ).lower()
    # “秋招提前批”必须优先归入提前批。
    for phase in ("提前批", "春招", "秋招"):
        if any(keyword.lower() in batch_text for keyword in PHASE_KEYWORDS[phase]):
            return phase
    return "未知"


def normalize_update_time(value: Any) -> str:
    """将平台常见的 ``YYYY/MM/DD`` 与 ISO 日期统一为可比较文本。"""
    return str(value or "").strip().replace("/", "-")


def normalize_platform_record(record: dict, nav: dict) -> dict:
    """Bridge stable internal field names across Offer 情报局 navigation revisions."""
    normalized = dict(record)
    if not str(normalized.get("企业名称", "")).strip():
        normalized["企业名称"] = str(normalized.get("招聘公告", "")).strip()
    if not str(normalized.get("毕业年份", "")).strip() and nav.get("graduation_year"):
        normalized["毕业年份"] = str(nav["graduation_year"])
    return normalized

# ============================================================
# 筛选模块
# ============================================================

class JobFilter:
    """岗位筛选器。纯函数，无副作用。"""

    FIELD_MAP = {
        "company": "企业名称",
        "company_type": "企业性质",
        "location": "工作地点",
        "position": "职位",
        "industry": "行业",
        "deadline": "截止时间",
        "education": "学历要求",
        "batch": "招聘批次",
        "graduation": "毕业年份",
        "apply_url": "投递地址",
        "announcement_url": "公告链接",
        "updated": "更新时间",
    }

    def __init__(self, config: dict, phase: str | None = None):
        self._filters = config.get("filters", {})
        self._phase = phase

    def passes(self, job: dict) -> bool:
        return all([
            self._match_any(job, "cities", "location"),
            self._match_none(job, "exclude_cities", "location"),
            self._match_any(job, "industries", "industry"),
            self._match_none(job, "exclude_industries", "industry"),
            self._match_any(job, "education_keywords", "education"),
            self._match_graduation(job),
            not self._phase or detect_phase(job) == self._phase,
        ])

    def score(self, job: dict) -> int:
        """按目标主线给出 0-100 的可解释初筛分，不替代人工选岗。"""
        s = 0
        loc = job.get(self.FIELD_MAP["location"], "")
        ind = job.get(self.FIELD_MAP["industry"], "")
        preferred_cities = self._filters.get("preferred_cities", []) or self._filters.get(
            "cities", []
        )
        location_bonus = 0
        matched_city = ""
        for index, city in enumerate(preferred_cities):
            if city and str(city).lower() in str(loc).lower():
                candidate_bonus = max(2, 10 - index)
                if candidate_bonus > location_bonus:
                    location_bonus = candidate_bonus
                    matched_city = str(city)
        s += location_bonus
        job["_preferred_city"] = matched_city
        job["_location_score"] = location_bonus
        if self._contains_any(ind, self._filters.get("industries", [])):
            s += 5
        if job.get(self.FIELD_MAP["graduation"], "") == "2027":
            s += 5

        matching = self._filters.get("matching", {})
        position = str(job.get(self.FIELD_MAP["position"], ""))
        corpus = " ".join(
            str(value) for key, value in job.items()
            if not str(key).startswith("_") and isinstance(value, (str, int, float))
        )
        primary_hits = self._matched_keywords(corpus, matching.get("primary_keywords", []))
        secondary_hits = self._matched_keywords(corpus, matching.get("secondary_keywords", []))
        title_hits = self._matched_keywords(position, matching.get("primary_keywords", []))
        negative_hits = self._matched_keywords(corpus, matching.get("deprioritize_keywords", []))

        s += min(45, len(primary_hits) * 9)
        s += min(20, len(secondary_hits) * 4)
        s += min(15, len(title_hits) * 5)
        s -= min(20, len(negative_hits) * 5)
        job["_match_reasons"] = primary_hits[:6] + secondary_hits[:4]
        job["_target_track"] = self.classify_track(corpus)
        return max(0, min(s, 100))

    def classify_track(self, text: str) -> str:
        matching = self._filters.get("matching", {})
        if self._matched_keywords(text, matching.get("primary_keywords", [])):
            return "具身智能"
        if self._matched_keywords(text, matching.get("secondary_keywords", [])):
            return "嵌入式/机器人系统"
        return "通用/观察"

    # ---- matchers ----
    def _match_any(self, job, filter_key, field_key):
        kws = self._filters.get(filter_key, [])
        if not kws:
            return True
        value = str(job.get(self.FIELD_MAP[field_key], "") or "").strip()
        # Offer 情报局的行业等辅助字段经常为空。字段缺失代表“未知”，
        # 不能当成“不匹配”，否则会把职位正文高度相关的记录全部漏掉。
        if not value:
            return True
        return self._contains_any(value, kws)

    def _match_none(self, job, filter_key, field_key):
        kws = self._filters.get(filter_key, [])
        if not kws:
            return True
        return not self._contains_any(job.get(self.FIELD_MAP[field_key], ""), kws)

    def _match_graduation(self, job):
        year = self._filters.get("graduation_year", "")
        if not year:
            return True
        graduation = str(job.get(self.FIELD_MAP["graduation"], "") or "")
        # 平台常以“2026,2027”或“2027届”表达多届可投，不能要求整串精确相等。
        # 部分新版导航只在导航名称中标注届别，单条记录缺字段时不可误判为不匹配。
        if not graduation.strip():
            return True
        return str(year) in graduation

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        if not text or not keywords:
            return bool(not keywords)
        return any(kw.lower() in text.lower() for kw in keywords)

    @staticmethod
    def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
        normalized = str(text or "").lower()
        return [keyword for keyword in keywords if str(keyword).lower() in normalized]


# ============================================================
# 输出
# ============================================================

def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ============================================================
# 增量抓取核心
# ============================================================

def fetch_navigation(
    api: OfferAPI,
    state: FetcherState,
    job_filter: JobFilter,
    tracker: ApplicationTracker,
    exclusions: ExclusionStore,
    nav: dict,
    max_records: int = 500,
    force_full: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    拉取单个导航的岗位数据。

    增量策略:
    - 全量模式 (首次/7天/强制): 遍历所有页
    - 增量模式: 从第1页开始，逐页检查。当某页所有记录更新时间 <= cutoff 时停止
    - 异常检测: 总数变化 >=15% 自动升级为全量
    """
    nav_id = nav["id"]
    nav_name = nav["name"]

    # 先获取第1页，检查是否需要全量
    first_page = api.fetch_jobs(nav_id, page=1)
    pagination = first_page.get("pagination", {})
    current_total = pagination.get("total_rows", 0)

    # 异常检测
    if not force_full and state.check_count_anomaly(nav_id, current_total):
        print(f"[fetch] ⚠️ {nav_name} 总数异常变化 ({current_total})，升级为全量同步",
              file=sys.stderr)
        force_full = True

    # 决定模式
    cutoff = state.get_cutoff(nav_id)
    if force_full:
        cutoff = None
        mode = "FULL"
    elif cutoff:
        mode = f"INCR (cutoff={cutoff[:10]})"
    else:
        mode = "FULL (首次)"

    print(f"[fetch] {nav_name} (id={nav_id}) 模式={mode} 总数={current_total}",
          file=sys.stderr)

    # 拉取
    all_records = []
    page = 1
    stopped_early = False
    seen_newest_update = None

    while len(all_records) < max_records:
        if page == 1:
            resp = first_page
        else:
            resp = api.fetch_jobs(nav_id, page=page)

        records = resp.get("data", [])
        if not records:
            break

        # 增量模式: 检查是否需要提前停止
        if cutoff and not force_full:
            # 记录本页最新 更新时间
            page_newest = max(
                (
                    normalize_update_time(
                        r.get(JobFilter.FIELD_MAP["updated"], "")
                    )
                    for r in records
                ),
                default="",
            )
            # 记录全局最新
            if not seen_newest_update or page_newest > seen_newest_update:
                seen_newest_update = page_newest

            # 检查本页是否全部是旧数据
            all_old = all(
                normalize_update_time(
                    r.get(JobFilter.FIELD_MAP["updated"], "1970-01-01")
                )
                <= normalize_update_time(cutoff)
                for r in records
            )
            if all_old and page > 1:
                print(
                    f"[fetch]   ⏹ 第{page}页全部为旧数据，停止 (共拉取{len(all_records)}条)",
                    file=sys.stderr,
                )
                stopped_early = True
                break

        all_records.extend(normalize_platform_record(record, nav) for record in records)

        # 检查是否还有下一页
        pagination = resp.get("pagination", {})
        if not pagination.get("has_next", False):
            break
        page += 1

    # 如果增量模式提前停止，用第1页最新时间作为 latest_update
    if stopped_early and seen_newest_update:
        effective_cutoff = seen_newest_update
    else:
        effective_cutoff = max(
            (
                normalize_update_time(
                    r.get(JobFilter.FIELD_MAP["updated"], "1970-01-01")
                )
                for r in all_records
            ),
            default=None,
        )

    # 全量同步只决定“遍历全部页面”，不代表历史岗位要重新输出。
    # 一旦建立版本历史，始终以内容指纹判断新增/变更；旧版状态文件
    # 没有指纹历史时，才回退到更新时间 cutoff。
    if state.has_seen_record_history():
        candidate_records = [
            job for job in all_records if not state.is_seen_record(job)
        ]
    elif cutoff and not force_full:
        candidate_records = [
            job
            for job in all_records
            if normalize_update_time(job.get(JobFilter.FIELD_MAP["updated"], ""))
            > normalize_update_time(cutoff)
        ]
    else:
        candidate_records = all_records

    # 筛选
    recent_companies = tracker.get_recent_companies(days=30)
    matched = []
    excluded_count = 0
    for job in candidate_records:
        exclusion = exclusions.match(job, phase=job_filter._phase or "")
        if exclusion:
            excluded_count += 1
            continue
        if not job_filter.passes(job):
            continue
        score = job_filter.score(job)
        job["_match_score"] = score
        job["_source"] = nav_name
        # 标记是否最近已投递过该公司
        if job.get(JobFilter.FIELD_MAP["company"], "") in recent_companies:
            job["_recent_action"] = "该公司30天内已有投递记录"
        matched.append(job)

    matched.sort(key=lambda j: j["_match_score"], reverse=True)

    # 去重
    seen = set()
    deduped = []
    for job in matched:
        url = job.get(JobFilter.FIELD_MAP["apply_url"], "")
        # 同时检查历史已投递 URL
        if url and (url in seen or state.is_applied(url)):
            continue
        seen.add(url)
        deduped.append(job)

    # dry-run 不推进 cutoff，也不污染已见版本状态。
    if not dry_run:
        state.remember_records(all_records)
        state.update(
            nav_id=nav_id,
            nav_name=nav_name,
            fetched_count=len(all_records),
            new_count=len(deduped),
            latest_update=effective_cutoff,
            total_rows=current_total,
        )

    return {
        "nav": nav,
        "fetched": len(all_records),
        "matched": len(matched),
        "deduped": len(deduped),
        "excluded": excluded_count,
        "records": deduped,
        "mode": mode,
        "total_rows": current_total,
    }


# ============================================================
# 编排
# ============================================================

def load_config() -> dict:
    config_path = SKILL_ROOT / "config.yaml"
    if not config_path.exists():
        print(f"[fetch] 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_fetch(
    config: dict,
    nav_id: int | None = None,
    force_full: bool = False,
    dry_run: bool = False,
    phase: str | None = None,
) -> dict:
    api_cfg = config.get("api", {})
    output_cfg = config.get("output", {})
    max_per_source = output_cfg.get("max_per_source", 500)

    api = OfferAPI(
        base_url=api_cfg.get("base_url", "https://offerqingbaoju.cn/api"),
        timeout=api_cfg.get("timeout", 30),
    )
    state = FetcherState()
    job_filter = JobFilter(config, phase=phase)
    tracker = ApplicationTracker()
    exclusions = ExclusionStore()

    navigations = config.get("navigations", [])
    if nav_id is not None:
        navigations = [n for n in navigations if n["id"] == nav_id]
    navigations = [n for n in navigations if n.get("enabled", True)]

    if not navigations:
        print("[fetch] 没有可用的数据源", file=sys.stderr)
        return {"total_fetched": 0, "total_matched": 0, "results": []}

    all_results = []
    total_fetched = 0
    total_new = 0

    for nav in navigations:
        result = fetch_navigation(
            api=api,
            state=state,
            job_filter=job_filter,
            tracker=tracker,
            exclusions=exclusions,
            nav=nav,
            max_records=max_per_source,
            force_full=force_full,
            dry_run=dry_run,
        )
        total_fetched += result["fetched"]
        total_new += result["deduped"]
        all_results.append(result)

        pct = (result["deduped"] / result["fetched"] * 100) if result["fetched"] else 0
        print(
            f"[fetch]   {result['mode']} → {result['fetched']}条→"
            f"排除{result['excluded']}→匹配{result['matched']}→"
            f"去重后{result['deduped']}条 ({pct:.0f}%)",
            file=sys.stderr,
        )

    # 汇总写入
    all_records = []
    for r in all_results:
        all_records.extend(r["records"])

    if not dry_run:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = PROJECT_ROOT / output_cfg.get("directory", "output")
        if phase:
            phase_file = {"提前批": "advance", "秋招": "autumn", "春招": "spring"}[phase]
            output_path = output_dir / f"{date_str}-offer-{phase_file}-jobs.jsonl"
        else:
            output_path = output_dir / f"{date_str}-jobs.jsonl"
        # 0 条增量也写空文件，避免 shortlist 误读上一轮结果。
        write_jsonl(all_records, output_path)
        print(f"[fetch] ✔ 已写入: {output_path} ({len(all_records)} 条)", file=sys.stderr)
    elif dry_run:
        print(f"[fetch] 🔍 预览模式: {len(all_records)} 条（未写入）", file=sys.stderr)

    return {
        "total_fetched": total_fetched,
        "total_new": total_new,
        "results": all_results,
    }


# ============================================================
# CLI
# ============================================================

def cmd_list_navigations(config: dict) -> None:
    api_cfg = config.get("api", {})
    api = OfferAPI(
        base_url=api_cfg.get("base_url", "https://offerqingbaoju.cn/api"),
        timeout=api_cfg.get("timeout", 30),
    )
    result = api.list_navigations()
    navs = result.get("navigations", [])
    print(f"{'ID':<6} {'名称':<20} {'记录数':<8} {'更新时间'}")
    print("-" * 60)
    for n in navs:
        print(
            f"{n['id']:<6} {n['name']:<20} {n.get('file_count', 0):<8} "
            f"{n.get('updated_at', 'N/A')}"
        )


def cmd_stats():
    state = FetcherState()
    summary = state.get_summary()
    if not summary:
        print("暂无抓取记录")
        return
    print(f"{'ID':<6} {'名称':<16} {'上次抓取':<22} {'总数':<6} {'上次新增'}")
    print("-" * 65)
    for nav_id, info in sorted(summary.items()):
        print(
            f"{nav_id:<6} {info['name']:<16} {str(info['last_fetch']):<22} "
            f"{info['total_rows']:<6} {info['last_new']}"
        )

    # 投递统计
    tracker = ApplicationTracker()
    print("\n" + tracker.daily_summary())


def main():
    parser = argparse.ArgumentParser(description="offer情报局 岗位拉取工具")
    parser.add_argument("--full-sync", action="store_true",
                        help="强制全量同步（默认增量）")
    parser.add_argument("--list-navigations", action="store_true",
                        help="列出可用数据源")
    parser.add_argument("--nav", type=int, help="只拉取指定导航ID")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览模式，不写文件")
    parser.add_argument("--stats", action="store_true",
                        help="查看抓取状态摘要")
    parser.add_argument("--save-token", type=str, help="保存 Bearer token")
    parser.add_argument("--check-token", action="store_true",
                        help="检查当前 token 状态")
    parser.add_argument("--wechat-login", action="store_true",
                        help="在终端显示二维码并完成微信扫码登录")
    parser.add_argument("--phase", choices=tuple(PHASE_KEYWORDS),
                        help="只保留指定招聘阶段；当前阶段使用 提前批")
    args = parser.parse_args()

    # token 操作
    if args.save_token:
        TokenManager().save_token(args.save_token)
        print("[fetch] Token 已保存")
        return
    if args.check_token:
        mgr = TokenManager()
        print("[fetch] Token 有效" if mgr.get_token() else "[fetch] Token 无效或已过期")
        return
    if args.wechat_login:
        from scripts.wechat_login import terminal_login
        raise SystemExit(terminal_login())

    config = load_config()

    if args.list_navigations:
        cmd_list_navigations(config)
        return

    if args.stats:
        cmd_stats()
        return

    # 权限检查
    mgr = TokenManager()
    if mgr.get_token() is None:
        print("[fetch] 请先运行 --wechat-login 完成终端扫码登录", file=sys.stderr)
        sys.exit(1)

    stats = run_fetch(
        config,
        nav_id=args.nav,
        force_full=args.full_sync,
        dry_run=args.dry_run,
        phase=args.phase,
    )

    # 汇总
    print(f"\n{'='*50}")
    print(f"总计: {stats['total_fetched']} 条 → 新增 {stats['total_new']} 条")
    for r in stats.get("results", []):
        print(
            f"  {r['nav']['name']} [{r['mode']}]: "
            f"{r['fetched']}条 → 新增{r['deduped']}条"
        )
    if args.dry_run:
        print("🔍 预览模式，未保存文件")


if __name__ == "__main__":
    main()
