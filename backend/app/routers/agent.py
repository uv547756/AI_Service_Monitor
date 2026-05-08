"""
Router: /agent — endpoints called BY the client agent.

POST /agent/report       — agent sends detected errors
POST /agent/result       — agent sends command execution results
GET  /agent/pending/{id} — agent polls for approved commands
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Machine, Log, Issue, Command, Execution
from ..schemas import AgentReportPayload, AgentResultPayload, CommandOut
from ..security import verify_api_key
from ..services import ai_engine, telegram_bot
from ..services.command_exec import validate_command

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"], dependencies=[Depends(verify_api_key)])


@router.post("/report")
async def agent_report(payload: AgentReportPayload, db: AsyncSession = Depends(get_db)):
    """
    Receive an error/warning report from a client agent.

    Flow: upsert machine → store log → AI analysis → create issue & command → Telegram alert.
    """
    # 1. Upsert machine
    result = await db.execute(select(Machine).where(Machine.hostname == payload.hostname))
    machine = result.scalar_one_or_none()

    if machine:
        # Update existing machine info
        machine.os_info = payload.system_info.os_info or machine.os_info
        machine.cpu = payload.system_info.cpu or machine.cpu
        machine.ram_total_gb = payload.system_info.ram_total_gb or machine.ram_total_gb
        machine.disk_total_gb = payload.system_info.disk_total_gb or machine.disk_total_gb
        machine.disk_used_pct = payload.system_info.disk_used_pct or machine.disk_used_pct
        machine.uptime = payload.system_info.uptime or machine.uptime
        machine.ip_address = payload.system_info.ip_address or machine.ip_address
        machine.last_seen = datetime.now(timezone.utc)
    else:
        machine = Machine(
            hostname=payload.hostname,
            os_info=payload.system_info.os_info,
            cpu=payload.system_info.cpu,
            ram_total_gb=payload.system_info.ram_total_gb,
            disk_total_gb=payload.system_info.disk_total_gb,
            disk_used_pct=payload.system_info.disk_used_pct,
            uptime=payload.system_info.uptime,
            ip_address=payload.system_info.ip_address,
        )
        db.add(machine)
        await db.flush()

    # 2. Store log
    log = Log(
        machine_id=machine.id,
        service=payload.service,
        severity=payload.severity,
        message=payload.trigger_message,
        raw_context=payload.log_context,
    )
    db.add(log)
    await db.flush()

    # 3. AI analysis
    system_summary = (
        f"CPU: {machine.cpu}, RAM: {machine.ram_total_gb}GB, "
        f"Disk: {machine.disk_used_pct}% used"
    )
    ai_result, raw_json = await ai_engine.analyze_log(
        trigger_message=payload.trigger_message,
        log_context=payload.log_context,
        service=payload.service,
        hostname=payload.hostname,
        os_info=machine.os_info,
        system_summary=system_summary,
    )

    # 4. Update machine status based on severity
    severity_status_map = {"critical": "critical", "high": "critical", "medium": "warning"}
    machine.status = severity_status_map.get(ai_result.severity, "warning")

    # 5. Create issue
    issue = Issue(
        machine_id=machine.id,
        log_id=log.id,
        service=payload.service,
        severity=ai_result.severity,
        confidence=ai_result.confidence,
        summary=ai_result.summary,
        root_cause=ai_result.root_cause,
        ai_raw_response=raw_json,
    )
    db.add(issue)
    await db.flush()

    # 6. Create command if AI recommended one
    command = None
    if ai_result.recommended_command:
        is_safe, reason = validate_command(ai_result.recommended_command)
        command = Command(
            issue_id=issue.id,
            machine_id=machine.id,
            command_text=ai_result.recommended_command,
            safe_to_auto_execute=ai_result.safe_to_auto_execute and is_safe,
        )
        db.add(command)
        await db.flush()

        # 7. Send Telegram alert
        tg_result = await telegram_bot.send_alert(
            machine_name=payload.hostname,
            severity=ai_result.severity,
            summary=ai_result.summary,
            command=ai_result.recommended_command,
            command_id=command.id,
        )
        if tg_result:
            command.telegram_message_id = tg_result["message_id"]
            command.telegram_chat_id = tg_result["chat_id"]

    await db.commit()

    return {
        "status": "received",
        "machine_id": machine.id,
        "issue_id": issue.id,
        "command_id": command.id if command else None,
        "severity": ai_result.severity,
        "summary": ai_result.summary,
    }


@router.post("/result")
async def agent_result(payload: AgentResultPayload, db: AsyncSession = Depends(get_db)):
    """Receive execution result from client agent."""
    command = await db.get(Command, payload.command_id)
    if not command:
        raise HTTPException(404, "Command not found")

    execution = Execution(
        command_id=command.id,
        status="success" if payload.exit_code == 0 else "failed",
        exit_code=payload.exit_code,
        stdout=payload.stdout,
        stderr=payload.stderr,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(execution)

    # Notify Telegram
    # Look up the machine hostname
    machine = await db.get(Machine, command.machine_id)
    hostname = machine.hostname if machine else "unknown"

    await telegram_bot.send_execution_result(
        machine_name=hostname,
        command_text=command.command_text,
        exit_code=payload.exit_code,
        stdout=payload.stdout,
        stderr=payload.stderr,
    )

    await db.commit()
    return {"status": "recorded", "execution_id": execution.id}


@router.get("/pending/{machine_id}")
async def get_pending_commands(machine_id: str, db: AsyncSession = Depends(get_db)):
    """Agent polls this to find approved commands awaiting execution."""
    result = await db.execute(
        select(Command)
        .where(Command.machine_id == machine_id, Command.approval_status == "approved")
    )
    commands = result.scalars().all()

    # Filter out commands that already have executions
    pending = []
    for cmd in commands:
        exec_result = await db.execute(
            select(Execution).where(Execution.command_id == cmd.id)
        )
        if not exec_result.scalar_one_or_none():
            pending.append(CommandOut.model_validate(cmd))

    return pending
