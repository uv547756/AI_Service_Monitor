from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

# THESE SCHEMAS DECIDE THE DATA FLOWING INTO THE LLM AS INPUT
# OUTPUT SCHEMA IS HANDLED BY THE SYS_PROMPT OF THE LLM FOR NOW
# TO-DO: make pydantic models to validate the output of the LLM


# This is what the LLM will take in it's prompt
class MachineContext(BaseModel):
    machine_id: str
    hostname: str
    os: str
    services: List[str] = Field(
        default_factory=list,
        )
    # Will decide to keep or remove later
    # arch: Optional[str] = None
    kernel_version: Optional[str] = None

class ErrorLog(BaseModel):
    source: str = Field(..., examples=["systemd"])
    service: Optional[str] = Field(None, examples=["nginx"])
    message: str
    raw_log: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unknown = "unknown"

class ErrorData(BaseModel):
    error_id: str
    severity: SeverityLevel = SeverityLevel.unknown
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    machine: MachineContext
    error: ErrorLog