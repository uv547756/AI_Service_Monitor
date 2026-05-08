"""
Router: /telegram — webhook endpoint for Telegram callback queries.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlalchemy import select

from ..database import async_session
from ..models import Command
from ..services import telegram_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle Telegram webhook updates (inline button callbacks).

    Expected callback_data format: "action:command_id"
    Actions: approve, reject, ignore
    """
    body = await request.json()
    callback_query = body.get("callback_query")
    if not callback_query:
        return {"ok": True}

    data = callback_query.get("data", "")
    callback_id = callback_query.get("id")
    user = callback_query.get("from", {})
    username = user.get("username", user.get("first_name", "unknown"))
    message = callback_query.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    message_id = message.get("message_id")
    original_text = message.get("text", "")

    if ":" not in data:
        return {"ok": True}

    action, command_id = data.split(":", 1)

    async with async_session() as db:
        command = await db.get(Command, command_id)
        if not command:
            await telegram_bot.answer_callback(callback_id, "⚠️ Command not found")
            return {"ok": True}

        if action == "approve":
            command.approval_status = "approved"
            command.approved_by = f"telegram:{username}"
            command.approved_at = datetime.now(timezone.utc)
            await telegram_bot.answer_callback(callback_id, "✅ Command approved!")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"✅ <b>APPROVED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s approved by %s", command_id, username)

        elif action == "reject":
            command.approval_status = "rejected"
            command.approved_by = f"telegram:{username}"
            command.approved_at = datetime.now(timezone.utc)
            await telegram_bot.answer_callback(callback_id, "❌ Command rejected")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"❌ <b>REJECTED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s rejected by %s", command_id, username)

        elif action == "ignore":
            await telegram_bot.answer_callback(callback_id, "🔇 Alert ignored")
            await telegram_bot.edit_message_markup(
                chat_id, message_id,
                new_text=f"🔇 <b>IGNORED</b> by @{username}\n\n{original_text}",
            )
            logger.info("Command %s ignored by %s", command_id, username)

        else:
            await telegram_bot.answer_callback(callback_id, "⚠️ Unknown action")

        await db.commit()

    return {"ok": True}
