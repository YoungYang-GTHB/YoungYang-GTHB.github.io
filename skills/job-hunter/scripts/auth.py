"""Offer 情报局会话管理：安全保存、校验并刷新 access token。"""

import sys
import json
import base64
from datetime import datetime, timezone
from pathlib import Path

import requests


class TokenManager:
    """管理 offer情报局 Bearer token 的存储和有效性校验。"""

    def __init__(
        self,
        token_path: str | None = None,
        session_path: str | None = None,
        base_url: str = "https://offerqingbaoju.cn/api",
    ):
        # 会话文件放在 skill 根目录，权限为 0600 且不进入 git。
        if token_path is None:
            token_path = Path(__file__).resolve().parent.parent / ".token"
        if session_path is None:
            session_path = Path(__file__).resolve().parent.parent / ".session.json"
        self._token_path = Path(token_path)
        self._session_path = Path(session_path)
        self._base_url = base_url.rstrip("/")

    # ---- public API ----

    def get_token(self) -> str | None:
        """返回有效 token，过期或不存在返回 None。"""
        session = self._load_session()
        token = str(session.get("access_token", "")).strip()
        if not token:
            return None
        if self._is_expired(token):
            refreshed = self.refresh_access_token(session)
            if refreshed:
                return refreshed
            print("[auth] 登录会话已失效，请重新扫码登录", file=sys.stderr)
            return None
        return token

    def save_token(self, token: str) -> None:
        """兼容旧命令：把手工 token 写入新的会话文件。"""
        self.save_session(token)

    def save_session(
        self,
        access_token: str,
        refresh_token: str = "",
        cookies: dict | None = None,
    ) -> None:
        """保存扫码登录得到的最小会话信息。"""
        payload = {
            "access_token": str(access_token).strip(),
            "refresh_token": str(refresh_token).strip(),
            "cookies": dict(cookies or {}),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._session_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._session_path.chmod(0o600)

    def refresh_access_token(self, session: dict | None = None) -> str | None:
        """复用网站前端的 /refresh 语义刷新短期 access token。"""
        current = session or self._load_session()
        access_token = str(current.get("access_token", "")).strip()
        if not access_token:
            return None

        try:
            session_client = requests.Session()
            session_client.trust_env = False
            response = session_client.post(
                f"{self._base_url}/refresh",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                cookies=current.get("cookies") or {},
                timeout=30,
            )
            if response.status_code != 200:
                return None
            payload = response.json()
            next_token = str(payload.get("access_token", "")).strip()
            if not next_token:
                return None
            merged_cookies = dict(current.get("cookies") or {})
            merged_cookies.update(response.cookies.get_dict())
            self.save_session(
                next_token,
                str(current.get("refresh_token", "")),
                merged_cookies,
            )
            return next_token
        except (requests.RequestException, ValueError):
            return None

    def check_and_warn(self) -> str | None:
        """获取 token，若无效则打印引导信息。返回有效 token 或 None。"""
        token = self.get_token()
        if token is None:
            self._print_how_to_get_token()
        return token

    # ---- internal ----

    def _load_session(self) -> dict:
        if self._session_path.exists():
            try:
                payload = json.loads(self._session_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except (OSError, ValueError):
                pass

        # 向后兼容旧版纯文本 .token，便于平滑迁移。
        if self._token_path.exists():
            token = self._token_path.read_text(encoding="utf-8").strip()
            if token:
                return {"access_token": token, "refresh_token": "", "cookies": {}}
        return {}

    @staticmethod
    def _is_expired(token: str) -> bool:
        """解码 JWT 检查 exp 是否已过。"""
        try:
            payload = token.split(".")[1]
            # 补齐 base64 padding
            payload += "=" * (-len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            exp = decoded.get("exp", 0)
            return datetime.now(timezone.utc).timestamp() > exp
        except Exception:
            # 无法解码则假定过期
            return True

    @staticmethod
    def _print_how_to_get_token() -> None:
        print(
            "[auth] 缺少有效会话。请在项目根目录运行终端扫码登录：\n"
            "  python3 skills/job-hunter/scripts/wechat_login.py",
            file=sys.stderr,
        )


# 便捷函数，供外部直接调用
def get_token() -> str | None:
    return TokenManager().check_and_warn()
