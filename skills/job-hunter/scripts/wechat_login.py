#!/usr/bin/env python3
"""在纯终端环境中完成 Offer 情报局微信扫码登录。"""

from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.auth import TokenManager


def extract_auth_payload(value) -> dict | None:
    """兼容接口外层 data/result 包装，定位登录成功载荷。"""
    if not isinstance(value, dict):
        return None
    if value.get("access_token"):
        return value
    for key in ("data", "result"):
        nested = extract_auth_payload(value.get(key))
        if nested:
            return nested
    return None


def decode_data_image(data_uri: str) -> bytes:
    if not isinstance(data_uri, str) or "," not in data_uri:
        raise ValueError("二维码图片格式无效")
    _, encoded = data_uri.split(",", 1)
    return base64.b64decode(encoded, validate=True)


def render_terminal_image(image_path: Path) -> bool:
    """优先使用 chafa，其次 img2txt；均不存在时返回 False。"""
    chafa = shutil.which("chafa")
    if chafa:
        subprocess.run(
            [chafa, "--format", "symbols", "--size", "60x30", str(image_path)],
            check=False,
        )
        return True

    img2txt = shutil.which("img2txt")
    if img2txt:
        subprocess.run([img2txt, "--width", "60", str(image_path)], check=False)
        return True
    return False


def terminal_login(
    base_url: str = "https://offerqingbaoju.cn/api",
    poll_interval: float = 2.0,
) -> int:
    api_base = base_url.rstrip("/")
    http = requests.Session()

    try:
        response = http.get(f"{api_base}/wechat/getLoginQRCode", timeout=30)
        response.raise_for_status()
        envelope = response.json()
        qr_data = envelope.get("data") or envelope
        state = str(qr_data.get("state", "")).strip()
        image_bytes = decode_data_image(qr_data.get("qrImage", ""))
        expires_in = int(qr_data.get("expireSeconds", 300) or 300)
        if not state:
            raise ValueError("二维码接口未返回登录状态标识")
    except (requests.RequestException, ValueError, TypeError) as exc:
        print(f"[login] 获取二维码失败：{exc}", file=sys.stderr)
        return 1

    qr_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="offer-wechat-", suffix=".jpg", delete=False
        ) as handle:
            handle.write(image_bytes)
            qr_path = Path(handle.name)
        qr_path.chmod(0o600)

        print("\n请使用微信扫描下方二维码（5 分钟内有效）：\n", file=sys.stderr)
        rendered = render_terminal_image(qr_path)
        if not rendered:
            print(
                "[login] 当前终端缺少 chafa/img2txt，二维码图片已暂存于："
                f"{qr_path}\n请用 scp 下载图片后扫码。",
                file=sys.stderr,
            )
        print("\n[login] 等待扫码确认，可按 Ctrl+C 取消…", file=sys.stderr)

        deadline = time.monotonic() + expires_in
        last_message = ""
        while time.monotonic() < deadline:
            try:
                status_response = http.post(
                    f"{api_base}/wechat/checkLoginStatus",
                    json={"state": state},
                    timeout=30,
                )
                status_response.raise_for_status()
                status_payload = status_response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[login] 状态检查暂时失败：{exc}", file=sys.stderr)
                time.sleep(poll_interval)
                continue

            auth_payload = extract_auth_payload(status_payload)
            if auth_payload:
                TokenManager(base_url=api_base).save_session(
                    access_token=str(auth_payload["access_token"]),
                    refresh_token=str(auth_payload.get("refresh_token", "")),
                    cookies=http.cookies.get_dict(),
                )
                print("\n[login] 微信登录成功，会话已安全保存（权限 0600）。")
                return 0

            message = str(status_payload.get("message", "等待扫码"))
            if message and message != last_message:
                print(f"[login] {message}", file=sys.stderr)
                last_message = message
            time.sleep(poll_interval)

        print("[login] 二维码已过期，请重新运行命令", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n[login] 已取消", file=sys.stderr)
        return 130
    finally:
        if qr_path:
            try:
                os.unlink(qr_path)
            except FileNotFoundError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="https://offerqingbaoju.cn/api",
        help="API 地址，通常无需修改",
    )
    parser.add_argument("--poll-interval", type=float, default=2.0)
    args = parser.parse_args()
    return terminal_login(args.base_url, max(1.0, args.poll_interval))


if __name__ == "__main__":
    raise SystemExit(main())
