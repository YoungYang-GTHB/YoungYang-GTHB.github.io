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
TAX_BRACKETS = (
    (36_000, 0.03, 0),
    (144_000, 0.10, 2_520),
    (300_000, 0.20, 16_920),
    (420_000, 0.25, 31_920),
    (660_000, 0.30, 52_920),
    (960_000, 0.35, 85_920),
    (float("inf"), 0.45, 181_920),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def annual_income_tax(taxable_yuan: float) -> float:
    """Annual resident comprehensive-income tax, after all allowed deductions."""
    amount = max(0, taxable_yuan)
    for ceiling, rate, quick_deduction in TAX_BRACKETS:
        if amount <= ceiling:
            return round(max(0, amount * rate - quick_deduction), 2)
    raise AssertionError("unreachable tax bracket")


def project_financial(offer: dict) -> dict | None:
    """Project annual cash savings from explicit, private offer assumptions.

    A 12-month employment-year convention is used for comparability. Contribution
    bases are simplified as annual gross pay; actual payroll bases and the split
    between salary and bonus require employer confirmation.
    """
    model = offer.get("financial_model")
    if model is None:
        return None
    gross_years = model["gross_income_wan"]
    require(isinstance(gross_years, list) and len(gross_years) == 3
            and all(isinstance(value, (int, float)) and value >= 0 for value in gross_years),
            f"{offer['id']} requires three non-negative annual gross amounts")
    require(model["rent_monthly_yuan"] >= 0, "monthly rent cannot be negative")
    result = {}
    for scenario_name in ("low", "base", "high"):
        scenario = model["scenarios"][scenario_name]
        rates = (scenario["social_rate"], scenario["housing_rate"], scenario["annuity_rate"])
        require(all(0 <= rate <= 1 for rate in rates) and sum(rates) < 1,
                f"{offer['id']}.{scenario_name} invalid personal contribution rates")
        require(scenario["rent_multiplier"] >= 0 and scenario["other_monthly_yuan"] >= 0,
                f"{offer['id']}.{scenario_name} invalid living expenses")
        annual_living = 12 * (model["rent_monthly_yuan"] * scenario["rent_multiplier"]
                              + scenario["other_monthly_yuan"])
        rent_deduction = 12 * scenario.get("rent_tax_deduction_monthly_yuan", 0)
        details = []
        for gross_wan in gross_years:
            gross_yuan = gross_wan * 10_000
            employee_contributions = gross_yuan * sum(rates)
            taxable = gross_yuan - employee_contributions - 60_000 - rent_deduction
            tax = annual_income_tax(taxable)
            cash = gross_yuan - employee_contributions - tax
            details.append({
                "gross_wan": gross_wan,
                "employee_contributions_wan": round(employee_contributions / 10_000, 3),
                "tax_wan": round(tax / 10_000, 3),
                "cash_wan": round(cash / 10_000, 3),
                "living_wan": round(annual_living / 10_000, 3),
                "savings_wan": round((cash - annual_living) / 10_000, 3),
            })
        result[scenario_name] = details
    for year in range(3):
        require(result["low"][year]["savings_wan"]
                <= result["base"][year]["savings_wan"]
                <= result["high"][year]["savings_wan"],
                f"{offer['id']} savings scenarios must be low <= base <= high")
    return result


def score_financial(offer: dict, anchors: dict, horizon_years: int = 3) -> dict | None:
    """Score the selected years of *liquid* savings, not gross package."""
    scenarios = offer.get("annual_net_savings_wan")
    if scenarios is None:
        return None
    require(isinstance(horizon_years, int) and 1 <= horizon_years <= 3,
            "financial scoring horizon must be 1, 2, or 3 years")
    floor, target = anchors["zero_wan"], anchors["full_wan"]
    require(isinstance(floor, (int, float)) and isinstance(target, (int, float))
            and target > floor, "financial anchors must have full_wan > zero_wan")

    def value(name: str) -> float:
        years = scenarios.get(name)
        require(isinstance(years, list) and len(years) == 3,
                f"annual_net_savings_wan.{name} requires exactly three years")
        require(all(isinstance(year, (int, float)) for year in years),
                f"annual_net_savings_wan.{name} must be numeric")
        annual_average = sum(years[:horizon_years]) / horizon_years
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
        projection = project_financial(offer)
        if projection is not None:
            require("annual_net_savings_wan" not in offer,
                    f"{offer['id']} cannot combine a financial model with manual savings")
            financial_input = {"annual_net_savings_wan": {
                scenario: [year["savings_wan"] for year in projection[scenario]]
                for scenario in ("low", "base", "high")
            }}
        else:
            financial_input = offer
        dimensions = {}
        for criterion in CRITERIA:
            if criterion == "financial":
                rating = score_financial(financial_input, data["financial_anchors"],
                                         data.get("financial_scoring_horizon_years", 3))
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
            "financial_projection": projection,
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
        f"财务分以首 {data.get('financial_scoring_horizon_years', 3)} 年税后收入减生活支出的低/中/高情景计算。"
        "税率全国统一；个人社保、公积金和年金费率及生活成本是各机会的明确假设。"
        "暂按连续12个月工作年、不适用专项附加扣除、奖金并入综合所得计算；实际工资条和自然年度税额可能不同。", "",
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
              + f"（原始权重合计 {common_weight:g}%）；各公司有缺失的指标不参与横向指数。", ""]
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
    projections = [row for row in rows if row["financial_projection"] is not None]
    if projections:
        lines += ["## 税后现金和结余测算", "",
                  "金额单位：万元/12个月工作年；不等同于自然年度发薪，不含未确认或受限补贴。", "",
                  "| 机会 | 首年税前 | 首年个人缴纳 | 首年个税 | 首年到手现金 | 首年生活支出 | 首年结余 | 第2/3年结余 |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in projections:
            years = row["financial_projection"]["base"]
            first = years[0]
            lines.append(
                f"| {row['offer']['label']} | {first['gross_wan']:.2f} | "
                f"{first['employee_contributions_wan']:.2f} | {first['tax_wan']:.2f} | "
                f"{first['cash_wan']:.2f} | {first['living_wan']:.2f} | "
                f"{first['savings_wan']:.2f} | "
                f"{years[1]['savings_wan']:.2f} / {years[2]['savings_wan']:.2f} |"
            )
        lines.append("")
        lines += ["模型统一以 55 平方米租房和每月 3,000 元非房租生活费为基准；"
                  "低/高情景只调整个人缴费假设及住房/其他支出，不代表工资涨跌预测。", ""]
        for row in projections:
            model = row["offer"]["financial_model"]
            lines.append(f"- {row['offer']['label']}住房假设：{model['rent_basis']}")
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
