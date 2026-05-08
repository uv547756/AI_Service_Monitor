"""
Telegram bot integration — sends alerts with inline approve/reject buttons
and processes callback responses.
"""
import logging
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Telegram Bot API base URL
_BASE = "https://api.telegram.org/bot{token}"


def _url(method: str) -> str:
    if not settings.TELEGRAM_BOT_TOKEN:
        return ""
    return f"{_BASE.format(token=settings.TELEGRAM_BOT_TOKEN)}/{method}"


async def send_alert(
    machine_name: str,
    severity: str,
    summary: str,
    command: str,
    command_id: str,
    chat_id: Optional[str] = None,
) -> Optional[dict]:
    """
    Send an alert message with Approve / Reject / Ignore inline buttons.

    Returns {"message_id": int, "chat_id": str} on success, None on failure.
    """
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID
    if not settings.TELEGRAM_BOT_TOKEN or not target_chat:
        logger.warning("Telegram not configured — skipping alert")
        return None

    severity_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    emoji = severity_emoji.get(severity, "⚪")

    text = (
        f"{emoji} <b>LogWatch Alert</b>\n\n"
        f"<b>Machine:</b> {machine_name}\n"
        f"<b>Severity:</b> {severity.upper()}\n"
        f"<b>Summary:</b> {summary}\n\n"
        f"<b>Suggested command:</b>\n<code>{command or 'None'}</code>"
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve:{command_id}"},
                {"text": "❌ Reject", "callback_data": f"reject:{command_id}"},
                {"text": "🔇 Ignore", "callback_data": f"ignore:{command_id}"},
            ]
        ]
    }

    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(_url("sendMessage"), json=payload)
            resp.raise_for_status()
            result = resp.json()
            msg_id = result.get("result", {}).get("message_id")
            logger.info("Telegram alert sent for command %s (msg_id=%s)", command_id, msg_id)
            return {"message_id": msg_id, "chat_id": target_chat}
    except Exception as e:
        logger.error("Failed to send Telegram alert: %s", e)
        return None


async def send_execution_result(
    machine_name: str,
    command_text: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    chat_id: Optional[str] = None,
) -> bool:
    """Notify Telegram about command execution results."""
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID
    if not settings.TELEGRAM_BOT_TOKEN or not target_chat:
        return False

    status_emoji = "✅" if exit_code == 0 else "❌"
    output = stdout[:1500] if stdout else stderr[:1500] if stderr else "No output"

    text = (
        f"{status_emoji} <b>Command Executed</b>\n\n"
        f"<b>Machine:</b> {machine_name}\n"
        f"<b>Command:</b> <code>{command_text}</code>\n"
        f"<b>Exit code:</b> {exit_code}\n\n"
        f"<b>Output:</b>\n<pre>{output}</pre>"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _url("sendMessage"),
                json={"chat_id": target_chat, "text": text, "parse_mode": "HTML"},
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to send execution result to Telegram: %s", e)
        return False


async def answer_callback(callback_query_id: str, text: str) -> bool:
    """Answer a Telegram inline button callback."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _url("answerCallbackQuery"),
                json={"callback_query_id": callback_query_id, "text": text},
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to answer callback: %s", e)
        return False


async def edit_message_markup(
    chat_id: str,
    message_id: int,
    new_text: Optional[str] = None,
    remove_buttons: bool = True,
) -> bool:
    """
    Edit a sent message — typically to remove inline buttons after an action.
    If new_text is provided, replaces the message text entirely.
    If remove_buttons is True, strips the inline keyboard.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if new_text:
                resp = await client.post(
                    _url("editMessageText"),
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": new_text,
                        "parse_mode": "HTML",
                    },
                )
            elif remove_buttons:
                resp = await client.post(
                    _url("editMessageReplyMarkup"),
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "reply_markup": {"inline_keyboard": []},
                    },
                )
            else:
                return True
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to edit Telegram message: %s", e)
        return False


async def register_webhook(webhook_url: str) -> bool:
    """
    Register a webhook URL with Telegram and delete any pending updates.
    Telegram will POST callback_query updates to this URL.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # First delete any existing webhook
            await client.post(_url("deleteWebhook"), json={"drop_pending_updates": True})

            # Set the new webhook
            resp = await client.post(
                _url("setWebhook"),
                json={
                    "url": webhook_url,
                    "allowed_updates": ["callback_query"],
                    "drop_pending_updates": True,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("ok"):
                logger.info("Webhook registered: %s", webhook_url)
                return True
            else:
                logger.error("Webhook registration failed: %s", result)
                return False
    except Exception as e:
        logger.error("Failed to register webhook: %s", e)
        return False
