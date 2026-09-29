#!/usr/bin/env python3
"""Evaluate private job-offer inputs without publishing their contents.

The input file belongs in the private career submodule. This script uses only the
Python standard library and never modifies an application ledger.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CRITERIA = (
    "financial",
    "technical",
    "stability",
    "city_family",
    "career_options",
    "work_environment",
)
LABELS = {
    "financial": "税后结余",
    "technical": "技术方向",
    "stability": "岗位稳定",
    "city_family": "城市/家庭",
    "career_options": "后续机会",
    "work_environment": "工作环境",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def score_financial(offer: dict, anchors: dict) -> dict | None:
    """Score three-year average annual *liquid* savings, not gross package."""
    scenarios = offer.get("annual_net_savings_wan")
    if scenarios is None:
        return None
    floor, target = anchors["zero_wan"], anchors["full_wan"]
    require(isinstance(floor, (int, float)) and isinstance(target, (int, float))
            and target > floor, "financial anchors must have full_wan > zero_wan")

    def value(name: str) -> float:
        years = scenarios.get(name)
        require(isinstance(years, list) and len(years) == 3,
                f"annual_net_savings_wan.{name} requires exactly three years")
        require(all(isinstance(year, (int, float)) for year in years),
                f"annual_net_savings_wan.{name} must be numeric")
        annual_average = sum(years) / 3
        return round(max(0, min(100, 100 * (annual_average - floor) / (target - floor))), 1)

    result = {"low": value("low"), "base": value("base"), "high": value("high")}
    require(result["low"] <= result["base"] <= result["high"],
            "financial low/base/high are not ordered")
    return result


def evaluate(data: dict) -> list[dict]:
    weights = data["weights"]
    require(set(weights) == set(CRITERIA), "weights must contain exactly six criteria")
    require(all(isinstance(weight, (int, float)) and weight >= 0 for weight in weights.values()),
            "weights must be non-negative numbers")
    require(abs(sum(weights.values()) - 100) < 1e-8, "weights must sum to 100")
    require(len({offer["id"] for offer in data["offers"]}) == len(data["offers"]),
            "offer ids must be unique")

    rows = []
    for offer in data["offers"]:
        dimensions = {}
        for criterion in CRITERIA:
            if criterion == "financial":
                rating = score_financial(offer, data["financial_anchors"])
            else:
                rating = offer.get("ratings", {}).get(criterion)
            if rating is not None:
                require(all(key in rating and isinstance(rating[key], (int, float))
                            for key in ("low", "base", "high")),
                        f"{offer['id']}.{criterion} requires low/base/high")
                require(0 <= rating["low"] <= rating["base"] <= rating["high"] <= 100,
                        f"{offer['id']}.{criterion} must be ordered scores in 0..100")
            dimensions[criterion] = rating

        covered_weight = sum(weights[key] for key, value in dimensions.items() if value is not None)
        require(covered_weight > 0, f"{offer['id']} has no scoreable dimensions")
        known_low = sum(weights[key] * value["low"] / 100 for key, value in dimensions.items()
                        if value is not None)
        known_base = sum(weights[key] * value["base"] / 100 for key, value in dimensions.items()
                         if value is not None)
        known_high = sum(weights[key] * value["high"] / 100 for key, value in dimensions.items()
                         if value is not None)
        rows.append({
            "offer": offer,
            "dimensions": dimensions,
            "covered_weight": covered_weight,
            "known_index": round(known_base / covered_weight * 100, 1),
            "total_low": round(known_low, 1),
            "total_high": round(known_high + 100 - covered_weight, 1),
        })
    return rows


def render(data: dict, rows: list[dict]) -> str:
    current_rows = [row for row in rows if row["offer"].get("current_candidate", True)]
    common_criteria = [
        key for key in CRITERIA
        if current_rows and all(row["dimensions"][key] is not None for row in current_rows)
    ]
    common_weight = sum(data["weights"][key] for key in common_criteria)

    def common_index(row: dict) -> str:
        if not common_weight:
            return "待核"
        weighted = sum(data["weights"][key] * row["dimensions"][key]["base"]
                       for key in common_criteria)
        return f"{weighted / common_weight:.1f}"

    lines = [
        "# Offer 量化比较（探索性）", "",
        f"基准日期：{data['as_of']}。权重是可调整的初值；非财务分数为分析假设，不是已证实的事实。", "",
        "财务分只在有逐年税后收入减生活支出的低/中/高三组数据时计算。"
        "缺失财务数据不会被填成零或估算净收入；总分区间将保留其全部未知范围。", "",
        "横向比较优先看‘共同指标指数’：所有近期机会都有数据的相同维度、相同权重口径。"
        "各自的已覆盖指标指数仅用于查看单项资料，覆盖率不同时不宜直接横比。", "",
    ]
    for title, selected in (
        ("近期已收到的机会（含有效性待核）", [row for row in rows if row["offer"].get("current_candidate", True)]),
        ("仅供历史参照，不参与当前排序", [row for row in rows if not row["offer"].get("current_candidate", True)]),
    ):
        if not selected:
            continue
        lines += [f"## {title}", "",
                  "| 机会 | 状态 | 共同指标指数/100 | 已覆盖权重 | 已覆盖指标指数/100 | 总分可行区间/100 |",
                  "|---|---|---:|---:|---:|---:|"]
        for row in selected:
            offer = row["offer"]
            lines.append(f"| {offer['label']} | {offer['status']} | {common_index(row)} | "
                         f"{row['covered_weight']:g}% | "
                         f"{row['known_index']:.1f} | {row['total_low']:.1f}–{row['total_high']:.1f} |")
        lines.append("")
    lines += ["共同指标：" + "、".join(LABELS[key] for key in common_criteria)
              + f"（原始权重合计 {common_weight:g}%）；不含缺失的薪酬与城市指标。", ""]
    lines += ["", "指标权重：" + "；".join(
        f"{LABELS[key]} {data['weights'][key]:g}%" for key in CRITERIA) + "。", "",
        "| 机会 | " + " | ".join(LABELS[key] for key in CRITERIA) + " |",
        "|---|" + "---:|" * len(CRITERIA),
    ]
    for row in rows:
        cells = []
        for key in CRITERIA:
            rating = row["dimensions"][key]
            cells.append("待核" if rating is None else
                         f"{rating['base']:g} [{rating['low']:g}–{rating['high']:g}]")
        lines.append("| " + row["offer"]["label"] + " | " + " | ".join(cells) + " |")
    lines += ["", "## 证据与待核项", ""]
    for row in rows:
        offer = row["offer"]
        lines += [f"### {offer['label']}", "", f"- 薪酬口径：{offer['compensation_note']}",
                  f"- 当前可选择性：{offer['eligibility_note']}"]
        for key in CRITERIA:
            if key != "financial":
                rating = offer.get("ratings", {}).get(key)
                if rating is not None:
                    lines.append(f"- {LABELS[key]}评分依据：{rating['basis']}")
        lines.append("")
    lines += ["## 使用限制", "",
              "- 已覆盖指标指数只比较有数据的指标，不是完整总分；总分区间重叠时不能宣称稳健排名。",
              "- 与 HR 书面报价、劳动合同或本人证实的信息冲突时，应先更新私有输入，不改动公开脚本。",
              "- 税后结余需按同等住房标准、通勤和个人支出分别估算三年；公积金和年金作为受限资产另列，不能重复计入可花现金。",
              "- 状态为待确认、过期或有效性待核的机会可以比较岗位价值，但不得视作目前可直接接受。",
              ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="private JSON comparison input")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    print(render(data, evaluate(data)))


if __name__ == "__main__":
    main()
