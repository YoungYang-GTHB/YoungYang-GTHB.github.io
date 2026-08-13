import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.api import OfferAPI


class OfferAPITests(unittest.TestCase):
    def test_offer_api_ignores_broken_global_proxy(self):
        api = OfferAPI()
        self.assertFalse(api._session.trust_env)


if __name__ == "__main__":
    unittest.main()
