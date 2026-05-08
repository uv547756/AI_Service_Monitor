"""
Telegram getUpdates polling loop.

Runs as a background task inside the FastAPI process. Polls Telegram for
callback_query updates (inline button presses) and processes them the same
way the webhook handler would — but without needing a public HTTPS URL.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx

from ..config import settings
from ..database import async_session
from ..models import Command
from . import telegram_bot

logger = logging.getLogger(__name__)

_running = True
_BASE = "https://api.telegram.org/bot{token}"


def _url(method: str) -> str:
    return f"{_BASE.format(token=settings.TELEGRAM_BOT_TOKEN)}/{method}"


def stop_polling():
    global _running
    _running = False


async def start_polling():
    """
    Long-poll Telegram's getUpdates endpoint. Processes callback_query
    updates from inline approve/reject/ignore buttons.
    """
    global _running
    offset = 0

    # Clear any existing webhook so getUpdates works
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(_url("deleteWebhook"))
            logger.info("Cleared any existing Telegram webhook")
    except Exception as e:
        logger.warning("Could not clear webhook: %s", e)

    while _running:
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                resp = await client.get(
                    _url("getUpdates"),
                    params={"offset": offset, "timeout": 30, "allowed_updates": '["callback_query"]'},
                )
                resp.raise_for_status()
                data = resp.json()

            if not data.get("ok"):
                logger.warning("Telegram getUpdates not ok: %s", data)
                await asyncio.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                callback_query = update.get("callback_query")
                if callback_query:
                    await _handle_callback(callback_query)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Telegram polling error: %s", e)
            await asyncio.sleep(5)


async def _handle_callback(callback_query: dict):
    """Process a single callback_query from an inline button press."""
    data = callback_query.get("data", "")
    callback_id = callback_query.get("id")
    user = callback_query.get("from", {})
    username = user.get("username", user.get("first_name", "unknown"))
    message = callback_query.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    message_id = message.get("message_id")
    original_text = message.get("text", "")

    if ":" not in data:
        return

    action, command_id = data.split(":", 1)

    async with async_session() as db:
        command = await db.get(Command, command_id)
        if not command:
            await telegram_bot.answer_callback(callback_id, "⚠️ Command not found")
            return

        if command.approval_status != "pending":
            await telegram_bot.answer_callback(
                callback_id,
                f"Already {command.approval_status} by {command.approved_by or 'someone'}",
            )
            # Still remove buttons from this message
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"ℹ️ <b>Already {command.approval_status.upper()}</b> by {command.approved_by}\n\n{original_text}",
            )
            return

        if action == "approve":
            command.approval_status = "approved"
            command.approved_by = f"telegram:{username}"
            command.approved_at = datetime.now(timezone.utc)
            await telegram_bot.answer_callback(callback_id, "✅ Command approved!")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"✅ <b>APPROVED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s approved by %s via Telegram", command_id, username)

        elif action == "reject":
            command.approval_status = "rejected"
            command.approved_by = f"telegram:{username}"
            command.approved_at = datetime.now(timezone.utc)
            await telegram_bot.answer_callback(callback_id, "❌ Command rejected")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"❌ <b>REJECTED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s rejected by %s via Telegram", command_id, username)

        elif action == "ignore":
            await telegram_bot.answer_callback(callback_id, "🔇 Alert ignored")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"🔇 <b>IGNORED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s ignored by %s via Telegram", command_id, username)

        else:
            await telegram_bot.answer_callback(callback_id, "⚠️ Unknown action")

        await db.commit()
