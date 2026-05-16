#!/usr/bin/env python3
"""Hook: gửi Telegram khi Claude Code kết thúc 1 lượt (Stop + Notification events).
Chạy tự động qua Claude Code hooks — không cần chạy tay.
"""
import json
import os
import sys
import urllib.request

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")


def send(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        payload = {}

    stop_reason = payload.get("stop_reason", "")
    notification_title = payload.get("title", "")
    notification_message = payload.get("message", "")

    # Notification event — Claude đang chờ permission từ người dùng
    if notification_title or notification_message:
        msg = notification_title or notification_message
        send(f"[Sicbo] Can phe duyet:\n{msg}\n\nMo VS Code de tiep tuc.")
        return

    # Stop event
    if stop_reason == "end_turn":
        send("Claude da xong luot lam viec.\nKiem tra VS Code de xem ket qua.")
    elif stop_reason == "max_tokens":
        send(
            "[Canh bao] Claude bi ngat giua chung (max tokens).\n"
            "Mo VS Code va noi: \"tiep tuc tu cho vua dung\""
        )
    elif stop_reason == "pause_turn":
        send("[Canh bao] Claude tam dung, can input. Mo VS Code de tiep tuc.")


if __name__ == "__main__":
    main()
