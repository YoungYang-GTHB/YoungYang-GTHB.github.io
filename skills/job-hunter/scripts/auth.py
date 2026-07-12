"""
Token 生命周期管理：加载、校验过期、提示刷新。

职责单一：只负责 token 的持久化和读取，不关心 API 细节。
"""

import os
import sys
import json
import base64
from datetime import datetime, timezone
from pathlib import Path


class TokenManager:
    """管理 offer情报局 Bearer token 的存储和有效性校验。"""

    def __init__(self, token_path: str | None = None):
        # token 文件放在 skill 根目录，不进入 git
        if token_path is None:
            token_path = Path(__file__).resolve().parent.parent / ".token"
        self._token_path = Path(token_path)

    # ---- public API ----

    def get_token(self) -> str | None:
        """返回有效 token，过期或不存在返回 None。"""
        token = self._load()
        if token is None:
            return None
        if self._is_expired(token):
            print("[auth] Token 已过期，请重新登录获取", file=sys.stderr)
            return None
        return token

    def save_token(self, token: str) -> None:
        """持久化 token 到文件。"""
        self._token_path.write_text(token.strip())
        self._token_path.chmod(0o600)

    def check_and_warn(self) -> str | None:
        """获取 token，若无效则打印引导信息。返回有效 token 或 None。"""
        token = self.get_token()
        if token is None:
            self._print_how_to_get_token()
        return token

    # ---- internal ----

    def _load(self) -> str | None:
        if not self._token_path.exists():
            return None
        token = self._token_path.read_text().strip()
        return token or None

    @staticmethod
    def _is_expired(token: str) -> bool:
        """解码 JWT 检查 exp 是否已过。"""
        try:
            payload = token.split(".")[1]
            # 补齐 base64 padding
            payload += "=" * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            exp = decoded.get("exp", 0)
            return datetime.now(timezone.utc).timestamp() > exp
        except Exception:
            # 无法解码则假定过期
            return True

    @staticmethod
    def _print_how_to_get_token() -> None:
        print(
            "[auth] 缺少有效 token，获取方式：\n"
            "  1. 浏览器打开 https://offerqingbaoju.cn 并登录\n"
            "  2. F12 → Application → Local Storage → offerqingbaoju.cn\n"
            "  3. 复制 token 的值\n"
            "  4. 在 skills/job-hunter/ 下运行:\n"
            "     python3 -c \"from scripts.auth import TokenManager; "
            "TokenManager().save_token('你的token')\"",
            file=sys.stderr,
        )


# 便捷函数，供外部直接调用
def get_token() -> str | None:
    return TokenManager().check_and_warn()
