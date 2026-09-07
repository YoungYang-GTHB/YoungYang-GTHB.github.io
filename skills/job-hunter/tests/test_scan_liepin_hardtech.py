import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.scan_liepin_hardtech import (
    build_report,
    close_target,
    is_known_company,
    load_known_companies,
    normalize_company,
    parse_card,
    scan_topic,
)


class LiepinHardtechScannerTests(unittest.TestCase):
    def test_close_target_uses_browser_cdp_connection(self):
        response = MagicMock()
        response.__enter__.return_value = BytesIO(
            b'{"webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/browser/browser-1"}'
        )
        browser = MagicMock()
        with patch(
            "scripts.scan_liepin_hardtech.urlopen", return_value=response
        ) as mocked_urlopen, patch(
            "scripts.scan_liepin_hardtech.CDPClient", return_value=browser
        ) as mocked_client:
            close_target("http://127.0.0.1:9222", "target-123")

        mocked_urlopen.assert_called_once_with(
            "http://127.0.0.1:9222/json/version", timeout=10
        )
        mocked_client.assert_called_once_with(
            "ws://127.0.0.1:9222/devtools/browser/browser-1"
        )
        browser.command.assert_called_once_with(
            "Target.closeTarget", {"targetId": "target-123"}
        )
        browser.close.assert_called_once_with()

    def test_scan_topic_closes_created_target_after_failure(self):
        page = MagicMock(target_id="target-456")
        page.evaluate.side_effect = RuntimeError("render failed")
        with patch(
            "scripts.scan_liepin_hardtech.open_target", return_value=page
        ), patch("scripts.scan_liepin_hardtech.close_target") as mocked_close:
            with self.assertRaisesRegex(RuntimeError, "render failed"):
                scan_topic("http://127.0.0.1:9222", "https://example.test/topic")

        mocked_close.assert_called_once_with("http://127.0.0.1:9222", "target-456")
        page.close.assert_called_once_with()

    def test_parse_card_extracts_name_id_and_count(self):
        card = {
            "text": "星海图\n具身智能与机器人B轮100-499人\n专注具身智能基础模型\n60个在招职位",
            "company_id": "12345",
        }
        parsed = parse_card(card)
        self.assertEqual(parsed["company"], "星海图")
        self.assertEqual(parsed["liepin_company_id"], "12345")
        self.assertEqual(parsed["open_position_count"], 60)

    def test_alias_deduplicates_known_company(self):
        known, matched = is_known_company("宇树科技(unitree)", ["宇树科技"])
        self.assertTrue(known)
        self.assertEqual(matched, "宇树科技")

        known, matched = is_known_company("北京格拉飞可斯科技有限公司", ["Meshy AI / 太极图形"])
        self.assertTrue(known)
        self.assertEqual(matched, "Meshy AI / 太极图形")

    def test_similar_but_different_company_is_not_merged(self):
        known, _ = is_known_company("极佳视界", ["极视角"])
        self.assertFalse(known)

    def test_report_marks_source_as_discovery_only(self):
        report = build_report(
            [{"company": "星海图", "liepin_company_id": "1", "summary": "具身智能世界模型", "open_position_count": 60}],
            [],
        )
        self.assertEqual(report["new_company_count"], 1)
        self.assertEqual(report["companies"][0]["evidence_level"], "discovery_only")
        self.assertTrue(report["companies"][0]["requires_official_2027_verification"])

    def test_normalization_removes_legal_suffixes(self):
        self.assertEqual(normalize_company("北京银河通用机器人有限公司"), "银河通用")

    def test_loads_companies_from_applications_and_monitors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "career/求职投递/2027届/data"
            data_dir.mkdir(parents=True)
            (data_dir / "applications.yaml").write_text(
                yaml.safe_dump({"applications": [{"company": "它石智航"}]}, allow_unicode=True),
                encoding="utf-8",
            )
            (data_dir / "monitoring.yaml").write_text(
                yaml.safe_dump({"monitors": [{"company": "小雨智造 XiaoyuBot"}]}, allow_unicode=True),
                encoding="utf-8",
            )
            self.assertEqual(load_known_companies(root), ["它石智航", "小雨智造 XiaoyuBot"])


if __name__ == "__main__":
    unittest.main()
