"""
Router: /logs — query logs with filters.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Log
from ..schemas import LogOut
from ..security import verify_api_key

router = APIRouter(prefix="/logs", tags=["logs"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=list[LogOut])
async def list_logs(
    machine_id: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Query logs with optional filters."""
    q = select(Log)

    if machine_id:
        q = q.where(Log.machine_id == machine_id)
    if service:
        q = q.where(Log.service == service)
    if severity:
        q = q.where(Log.severity == severity)

    q = q.order_by(Log.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()
