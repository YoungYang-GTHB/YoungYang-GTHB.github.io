import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("evaluate.py")
SPEC = importlib.util.spec_from_file_location("offer_evaluate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OfferEvaluationTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            "weights": {
                "financial": 25,
                "technical": 30,
                "stability": 15,
                "city_family": 15,
                "career_options": 10,
                "work_environment": 5,
            },
            "financial_anchors": {"zero_wan": 3, "full_wan": 20},
            "offers": [{
                "id": "sample",
                "ratings": {
                    key: {"low": 40, "base": 50, "high": 60, "basis": "sample"}
                    for key in MODULE.CRITERIA if key != "financial"
                },
            }],
        }

    def test_missing_financial_is_unknown_not_zero(self):
        result = MODULE.evaluate(self.data)[0]
        self.assertEqual(result["covered_weight"], 75)
        self.assertEqual(result["known_index"], 50)
        self.assertEqual(result["total_low"], 30)
        self.assertEqual(result["total_high"], 70)

    def test_financial_three_year_average(self):
        self.data["offers"][0]["annual_net_savings_wan"] = {
            "low": [3, 3, 3],
            "base": [11.5, 11.5, 11.5],
            "high": [20, 20, 20],
        }
        result = MODULE.evaluate(self.data)[0]
        self.assertEqual(result["dimensions"]["financial"],
                         {"low": 0, "base": 50, "high": 100})
        self.assertEqual(result["covered_weight"], 100)
        self.assertEqual(result["known_index"], 50)

    def test_first_year_financial_score_ignores_unconfirmed_later_pay(self):
        self.data["financial_scoring_horizon_years"] = 1
        self.data["offers"][0]["annual_net_savings_wan"] = {
            "low": [3, 20, 20],
            "base": [3, 20, 20],
            "high": [3, 20, 20],
        }
        result = MODULE.evaluate(self.data)[0]
        self.assertEqual(result["dimensions"]["financial"]["base"], 0)
        self.assertEqual(result["known_index"], 37.5)

    def test_weights_must_sum_to_one_hundred(self):
        self.data["weights"]["technical"] = 31
        with self.assertRaisesRegex(ValueError, "sum to 100"):
            MODULE.evaluate(self.data)

    def test_annual_tax_brackets(self):
        self.assertEqual(MODULE.annual_income_tax(-1), 0)
        self.assertEqual(MODULE.annual_income_tax(36_000), 1_080)
        self.assertEqual(MODULE.annual_income_tax(100_000), 7_480)
        self.assertEqual(MODULE.annual_income_tax(144_000), 11_880)

    def test_financial_model_projects_cash_and_savings(self):
        self.data["offers"][0]["financial_model"] = {
            "gross_income_wan": [12, 12, 12],
            "rent_monthly_yuan": 1000,
            "scenarios": {
                "low": {"social_rate": 0.1, "housing_rate": 0.12,
                        "annuity_rate": 0, "rent_multiplier": 1.25,
                        "other_monthly_yuan": 3000},
                "base": {"social_rate": 0.1, "housing_rate": 0.08,
                         "annuity_rate": 0, "rent_multiplier": 1,
                         "other_monthly_yuan": 2000},
                "high": {"social_rate": 0.1, "housing_rate": 0.05,
                         "annuity_rate": 0, "rent_multiplier": 0.75,
                         "other_monthly_yuan": 1500},
            },
        }
        result = MODULE.evaluate(self.data)[0]
        base = result["financial_projection"]["base"][0]
        self.assertEqual(base["employee_contributions_wan"], 2.16)
        self.assertEqual(base["tax_wan"], 0.132)
        self.assertEqual(base["cash_wan"], 9.708)
        self.assertEqual(base["living_wan"], 3.6)
        self.assertEqual(base["savings_wan"], 6.108)


if __name__ == "__main__":
    unittest.main()
