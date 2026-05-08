"""
Router: /machines — list machines, get machine details.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Machine, Issue, Log
from ..schemas import MachineOut
from ..security import verify_api_key

router = APIRouter(prefix="/machines", tags=["machines"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=list[MachineOut])
async def list_machines(db: AsyncSession = Depends(get_db)):
    """Get all registered machines."""
    result = await db.execute(select(Machine).order_by(Machine.last_seen.desc()))
    return result.scalars().all()


@router.get("/{machine_id}")
async def get_machine(machine_id: str, db: AsyncSession = Depends(get_db)):
    """Get machine details including recent logs and issue counts."""
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise HTTPException(404, "Machine not found")

    # Recent logs (last 50)
    logs_q = await db.execute(
        select(Log)
        .where(Log.machine_id == machine_id)
        .order_by(Log.timestamp.desc())
        .limit(50)
    )
    recent_logs = logs_q.scalars().all()

    # Issue counts
    issues_q = await db.execute(
        select(Issue.status, func.count(Issue.id))
        .where(Issue.machine_id == machine_id)
        .group_by(Issue.status)
    )
    issue_counts = {row[0]: row[1] for row in issues_q.all()}

    return {
        "machine": MachineOut.model_validate(machine),
        "recent_logs": [
            {
                "id": l.id,
                "service": l.service,
                "severity": l.severity,
                "message": l.message,
                "timestamp": l.timestamp,
            }
            for l in recent_logs
        ],
        "issue_counts": issue_counts,
    }
