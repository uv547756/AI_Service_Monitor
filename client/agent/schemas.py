from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import Literal
from datetime import datetime, timezone
from enum import Enum

# --- Shared Enums & Sub-models ---

class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unknown = "unknown"

class MachineContext(BaseModel):
    machine_id: str
    hostname: str
    os: str
    services: List[str] = Field(default_factory=list)
    kernel_version: Optional[str] = None

class ErrorLog(BaseModel):
    source: str
    service: Optional[str] = None
    message: str
    raw_log: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Data Transfer Objects ---

class ErrorData(BaseModel):
    """
    Data payload sent from Client to Backend.
    """
    error_id: str
    severity: SeverityLevel = SeverityLevel.unknown
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    machine: MachineContext
    error: ErrorLog

class FixCommand(BaseModel):
    command: str
    explanation: str
    risk_level: Literal["low", "medium", "high"]
    expected_output: str
    requires_sudo: bool = False
    confidence: Optional[str] = None

class AnalysisResult(BaseModel):
    """
    Response received from Backend (after polling/approval).
    """
    diagnosis: str
    commands: List[FixCommand]
    verification: str

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