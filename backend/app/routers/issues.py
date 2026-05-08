"""
Router: /issues — list issues, get issue details.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Issue, Command, Execution
from ..schemas import IssueOut, CommandOut, ExecutionOut
from ..security import verify_api_key

router = APIRouter(prefix="/issues", tags=["issues"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=list[IssueOut])
async def list_issues(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List issues with optional filters."""
    q = select(Issue)
    if severity:
        q = q.where(Issue.severity == severity)
    if status:
        q = q.where(Issue.status == status)
    if machine_id:
        q = q.where(Issue.machine_id == machine_id)

    q = q.order_by(Issue.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{issue_id}")
async def get_issue(issue_id: str, db: AsyncSession = Depends(get_db)):
    """Get full issue details with log context, AI analysis, and commands."""
    result = await db.execute(
        select(Issue)
        .options(
            selectinload(Issue.machine),
            selectinload(Issue.trigger_log),
            selectinload(Issue.commands).selectinload(Command.executions),
        )
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(404, "Issue not found")

    commands = []
    for cmd in issue.commands:
        cmd_data = CommandOut.model_validate(cmd).model_dump()
        cmd_data["executions"] = [
            ExecutionOut.model_validate(ex).model_dump() for ex in cmd.executions
        ]
        commands.append(cmd_data)

    return {
        "id": issue.id,
        "machine_id": issue.machine_id,
        "machine": {
            "hostname": issue.machine.hostname if issue.machine else None,
            "status": issue.machine.status if issue.machine else None,
        },
        "log_id": issue.log_id,
        "trigger_log": {
            "message": issue.trigger_log.message if issue.trigger_log else None,
            "raw_context": issue.trigger_log.raw_context if issue.trigger_log else None,
            "service": issue.trigger_log.service if issue.trigger_log else None,
            "severity": issue.trigger_log.severity if issue.trigger_log else None,
            "timestamp": issue.trigger_log.timestamp if issue.trigger_log else None,
        } if issue.trigger_log else None,
        "service": issue.service,
        "severity": issue.severity,
        "confidence": issue.confidence,
        "summary": issue.summary,
        "root_cause": issue.root_cause,
        "ai_raw_response": issue.ai_raw_response,
        "status": issue.status,
        "created_at": issue.created_at,
        "commands": commands,
    }
