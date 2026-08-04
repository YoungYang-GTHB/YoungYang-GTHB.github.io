import base64
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.auth import TokenManager
from scripts.wechat_login import decode_data_image, extract_auth_payload


class WechatLoginTests(unittest.TestCase):
    def test_extract_auth_payload_accepts_nested_api_response(self):
        payload = {
            "code": 0,
            "data": {"access_token": "access", "refresh_token": "refresh"},
        }
        self.assertEqual(extract_auth_payload(payload)["access_token"], "access")
        self.assertIsNone(extract_auth_payload({"code": 1002, "message": "未登录"}))

    def test_decode_data_image(self):
        encoded = base64.b64encode(b"jpeg-bytes").decode("ascii")
        self.assertEqual(decode_data_image(f"data:image/jpeg;base64,{encoded}"), b"jpeg-bytes")

    def test_session_file_is_private_and_contains_no_user_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / ".session.json"
            manager = TokenManager(
                token_path=str(Path(temp_dir) / ".token"),
                session_path=str(session_path),
            )
            manager.save_session("access", "refresh", {"session": "cookie"})

            mode = stat.S_IMODE(session_path.stat().st_mode)
            payload = json.loads(session_path.read_text(encoding="utf-8"))
            self.assertEqual(mode, 0o600)
            self.assertEqual(payload["access_token"], "access")
            self.assertNotIn("user", payload)


if __name__ == "__main__":
    unittest.main()
