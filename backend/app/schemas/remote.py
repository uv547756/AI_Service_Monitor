from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum

class JobType(str, Enum):
    GET_STATUS = "GET_STATUS"
    GET_LOGS = "GET_LOGS"
    EXEC_CMD = "EXEC_CMD"

class Job(BaseModel):
    job_id: str
    type: JobType
    args: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HeartbeatRequest(BaseModel):
    machine_id: str
    hostname: str
    services: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HeartbeatResponse(BaseModel):
    pending_jobs: List[Job]

class JobResult(BaseModel):
    job_id: str
    machine_id: str
    output: str
    success: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FixResult(BaseModel):
    error_id: str
    success: bool
    log: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
