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
        s = 0
        loc = job.get(self.FIELD_MAP["location"], "")
        ind = job.get(self.FIELD_MAP["industry"], "")
        if self._contains_any(loc, self._filters.get("cities", [])):
            s += 2
        if self._contains_any(ind, self._filters.get("industries", [])):
            s += 2
        if job.get(self.FIELD_MAP["graduation"], "") == "2027":
            s += 1
        return min(s, 5)

    # ---- matchers ----
    def _match_any(self, job, filter_key, field_key):
        kws = self._filters.get(filter_key, [])
        if not kws:
            return True
        return self._contains_any(job.get(self.FIELD_MAP[field_key], ""), kws)

    def _match_none(self, job, filter_key, field_key):
        kws = self._filters.get(filter_key, [])
        if not kws:
            return True
        return not self._contains_any(job.get(self.FIELD_MAP[field_key], ""), kws)

    def _match_graduation(self, job):
        year = self._filters.get("graduation_year", "")
        if not year:
            return True
        return job.get(self.FIELD_MAP["graduation"], "") == year

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        if not text or not keywords:
            return bool(not keywords)
        return any(kw.lower() in text.lower() for kw in keywords)


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
                (r.get(JobFilter.FIELD_MAP["updated"], "") for r in records),
                default="",
            )
            # 记录全局最新
            if not seen_newest_update or page_newest > seen_newest_update:
                seen_newest_update = page_newest

            # 检查本页是否全部是旧数据
            all_old = all(
                r.get(JobFilter.FIELD_MAP["updated"], "1970-01-01") <= cutoff
                for r in records
            )
            if all_old and page > 1:
                print(
                    f"[fetch]   ⏹ 第{page}页全部为旧数据，停止 (共拉取{len(all_records)}条)",
                    file=sys.stderr,
                )
                stopped_early = True
                break

        all_records.extend(records)

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
            (r.get(JobFilter.FIELD_MAP["updated"], "1970-01-01")
             for r in all_records),
            default=None,
        )

    # 筛选
    recent_companies = tracker.get_recent_companies(days=30)
    matched = []
    for job in all_records:
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

    # 更新状态
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
            f"匹配{result['matched']}→去重后{result['deduped']}条 ({pct:.0f}%)",
            file=sys.stderr,
        )

    # 汇总写入
    all_records = []
    for r in all_results:
        all_records.extend(r["records"])

    if not dry_run and all_records:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = PROJECT_ROOT / output_cfg.get("directory", "output")
        if phase:
            phase_file = {"提前批": "advance", "秋招": "autumn", "春招": "spring"}[phase]
            output_path = output_dir / f"{date_str}-offer-{phase_file}-jobs.jsonl"
        else:
            output_path = output_dir / f"{date_str}-jobs.jsonl"
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
