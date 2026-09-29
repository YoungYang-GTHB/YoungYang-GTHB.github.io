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

    def test_weights_must_sum_to_one_hundred(self):
        self.data["weights"]["technical"] = 31
        with self.assertRaisesRegex(ValueError, "sum to 100"):
            MODULE.evaluate(self.data)


if __name__ == "__main__":
    unittest.main()
