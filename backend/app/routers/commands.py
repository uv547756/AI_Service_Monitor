"""
Router: /commands — list, approve, and reject commands.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Command, Execution
from ..schemas import CommandOut, ExecutionOut
from ..security import verify_api_key
from ..services import telegram_bot

router = APIRouter(prefix="/commands", tags=["commands"], dependencies=[Depends(verify_api_key)])


@router.get("")
async def list_commands(
    approval_status: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List all commands with their executions."""
    q = select(Command).options(selectinload(Command.executions))
    if approval_status:
        q = q.where(Command.approval_status == approval_status)
    if machine_id:
        q = q.where(Command.machine_id == machine_id)

    q = q.order_by(Command.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    commands = result.scalars().all()

    return [
        {
            **CommandOut.model_validate(cmd).model_dump(),
            "executions": [
                ExecutionOut.model_validate(ex).model_dump() for ex in cmd.executions
            ],
        }
        for cmd in commands
    ]


@router.patch("/{command_id}/approve")
async def approve_command(command_id: str, db: AsyncSession = Depends(get_db)):
    """Approve a pending command from the dashboard — also updates Telegram."""
    result = await db.execute(select(Command).where(Command.id == command_id))
    cmd = result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    if cmd.approval_status != "pending":
        raise HTTPException(status_code=400, detail=f"Command is already {cmd.approval_status}")

    cmd.approval_status = "approved"
    cmd.approved_by = "dashboard"
    cmd.approved_at = datetime.now(timezone.utc)

    # Sync to Telegram — edit the alert message to remove buttons
    if cmd.telegram_message_id and cmd.telegram_chat_id:
        await telegram_bot.edit_message_markup(
            chat_id=cmd.telegram_chat_id,
            message_id=cmd.telegram_message_id,
            new_text=f"✅ <b>APPROVED</b> via dashboard\n\n<b>Command:</b>\n<code>{cmd.command_text}</code>",
        )

    await db.commit()
    await db.refresh(cmd)
    return CommandOut.model_validate(cmd).model_dump()


@router.patch("/{command_id}/reject")
async def reject_command(command_id: str, db: AsyncSession = Depends(get_db)):
    """Reject a pending command from the dashboard — also updates Telegram."""
    result = await db.execute(select(Command).where(Command.id == command_id))
    cmd = result.scalar_one_or_none()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    if cmd.approval_status != "pending":
        raise HTTPException(status_code=400, detail=f"Command is already {cmd.approval_status}")

    cmd.approval_status = "rejected"
    cmd.approved_by = "dashboard"
    cmd.approved_at = datetime.now(timezone.utc)

    # Sync to Telegram — edit the alert message to remove buttons
    if cmd.telegram_message_id and cmd.telegram_chat_id:
        await telegram_bot.edit_message_markup(
            chat_id=cmd.telegram_chat_id,
            message_id=cmd.telegram_message_id,
            new_text=f"❌ <b>REJECTED</b> via dashboard\n\n<b>Command:</b>\n<code>{cmd.command_text}</code>",
        )

    await db.commit()
    await db.refresh(cmd)
    return CommandOut.model_validate(cmd).model_dump()
