#!/usr/bin/env python3
"""
Telegram MCP Server cho Claude Code
Cho phép Claude Code giao task, nhận phản hồi, và hỏi status qua Telegram.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

server = Server("telegram-sicbo")


async def call_telegram(method: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{TELEGRAM_API}/{method}", json=payload)
        resp.raise_for_status()
        return resp.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="telegram_send_task",
            description=(
                "Giao task cho team qua Telegram. "
                "Dùng khi bắt đầu một task mới để thông báo cho admin."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Tên task đang bắt đầu",
                    },
                    "description": {
                        "type": "string",
                        "description": "Mô tả chi tiết task",
                    },
                    "estimated_time": {
                        "type": "string",
                        "description": "Thời gian ước tính (ví dụ: 30 phút, 2 giờ)",
                    },
                },
                "required": ["task_name", "description"],
            },
        ),
        Tool(
            name="telegram_report_done",
            description=(
                "Báo cáo task đã hoàn thành qua Telegram. "
                "Dùng sau khi hoàn thành một task để thông báo cho admin."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "Tên task vừa hoàn thành",
                    },
                    "result": {
                        "type": "string",
                        "description": "Kết quả/tóm tắt những gì đã làm",
                    },
                    "files_changed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sách file đã tạo/sửa (tùy chọn)",
                    },
                },
                "required": ["task_name", "result"],
            },
        ),
        Tool(
            name="telegram_report_status",
            description=(
                "Báo cáo status hiện tại của dự án qua Telegram. "
                "Dùng khi cần update tiến độ cho admin."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status_message": {
                        "type": "string",
                        "description": "Nội dung status update",
                    },
                    "phase": {
                        "type": "string",
                        "description": "Phase hiện tại (ví dụ: Phase 1 - Foundation)",
                    },
                    "progress_percent": {
                        "type": "number",
                        "description": "Phần trăm hoàn thành (0-100)",
                    },
                },
                "required": ["status_message"],
            },
        ),
        Tool(
            name="telegram_get_messages",
            description=(
                "Lấy tin nhắn mới nhất từ admin trên Telegram. "
                "Dùng để check xem admin có phản hồi hoặc yêu cầu gì không."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng tin nhắn cần lấy (mặc định: 5)",
                        "default": 5,
                    }
                },
            },
        ),
        Tool(
            name="telegram_send_error",
            description=(
                "Báo lỗi cho admin qua Telegram khi gặp vấn đề không tự giải quyết được."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "error_context": {
                        "type": "string",
                        "description": "Đang làm gì khi gặp lỗi",
                    },
                    "error_message": {
                        "type": "string",
                        "description": "Nội dung lỗi",
                    },
                    "question": {
                        "type": "string",
                        "description": "Câu hỏi cần admin trả lời để tiếp tục",
                    },
                },
                "required": ["error_context", "error_message"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    now = datetime.now().strftime("%H:%M %d/%m/%Y")

    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return [TextContent(
            type="text",
            text="❌ Lỗi: TELEGRAM_BOT_TOKEN hoặc TELEGRAM_ADMIN_CHAT_ID chưa được cấu hình."
        )]

    if name == "telegram_send_task":
        task_name = arguments["task_name"]
        description = arguments["description"]
        estimated = arguments.get("estimated_time", "Không xác định")

        text = (
            f"🚀 *TASK MỚI BẮT ĐẦU*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Task:* {task_name}\n"
            f"📝 *Mô tả:* {description}\n"
            f"⏱ *Ước tính:* {estimated}\n"
            f"🕐 *Lúc:* {now}"
        )
        result = await call_telegram("sendMessage", {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        })
        return [TextContent(type="text", text=f"✅ Đã gửi task '{task_name}' cho admin qua Telegram.")]

    elif name == "telegram_report_done":
        task_name = arguments["task_name"]
        result_text = arguments["result"]
        files = arguments.get("files_changed", [])

        files_section = ""
        if files:
            files_list = "\n".join(f"  • `{f}`" for f in files[:10])
            files_section = f"\n📁 *Files đã thay đổi:*\n{files_list}"

        text = (
            f"✅ *TASK HOÀN THÀNH*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Task:* {task_name}\n"
            f"📊 *Kết quả:* {result_text}"
            f"{files_section}\n"
            f"🕐 *Lúc:* {now}"
        )
        await call_telegram("sendMessage", {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        })
        return [TextContent(type="text", text=f"✅ Đã báo cáo hoàn thành task '{task_name}'.")]

    elif name == "telegram_report_status":
        message = arguments["status_message"]
        phase = arguments.get("phase", "")
        progress = arguments.get("progress_percent")

        phase_section = f"\n🎯 *Phase:* {phase}" if phase else ""
        progress_section = f"\n📈 *Tiến độ:* {progress}%" if progress is not None else ""

        text = (
            f"📊 *STATUS UPDATE*\n"
            f"━━━━━━━━━━━━━━━━━━"
            f"{phase_section}"
            f"{progress_section}\n"
            f"💬 {message}\n"
            f"🕐 *Lúc:* {now}"
        )
        await call_telegram("sendMessage", {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        })
        return [TextContent(type="text", text="✅ Đã gửi status update.")]

    elif name == "telegram_get_messages":
        limit = arguments.get("limit", 5)
        result = await call_telegram("getUpdates", {
            "limit": limit,
            "allowed_updates": ["message"],
        })
        updates = result.get("result", [])
        if not updates:
            return [TextContent(type="text", text="📭 Không có tin nhắn mới từ admin.")]

        messages = []
        for update in updates:
            msg = update.get("message", {})
            text_content = msg.get("text", "")
            from_user = msg.get("from", {}).get("first_name", "Unknown")
            date_ts = msg.get("date", 0)
            messages.append(f"[{from_user}]: {text_content}")

        return [TextContent(
            type="text",
            text="📬 Tin nhắn mới:\n" + "\n".join(messages)
        )]

    elif name == "telegram_send_error":
        context = arguments["error_context"]
        error = arguments["error_message"]
        question = arguments.get("question", "")

        question_section = f"\n❓ *Câu hỏi:* {question}" if question else ""

        text = (
            f"⚠️ *GẶP VẤN ĐỀ - CẦN HỖ TRỢ*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 *Đang làm:* {context}\n"
            f"❌ *Lỗi:* {error}"
            f"{question_section}\n"
            f"🕐 *Lúc:* {now}"
        )
        await call_telegram("sendMessage", {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        })
        return [TextContent(type="text", text="✅ Đã báo lỗi cho admin. Chờ phản hồi.")]

    return [TextContent(type="text", text=f"❌ Tool không xác định: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
