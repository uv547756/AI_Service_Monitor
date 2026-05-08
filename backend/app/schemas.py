"""
Pydantic schemas for request/response serialization.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class MachineBase(BaseModel):
    hostname: str
    os_info: Optional[str] = None
    cpu: Optional[str] = None
    ram_total_gb: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_pct: Optional[float] = None
    uptime: Optional[str] = None
    ip_address: Optional[str] = None


class MachineOut(MachineBase):
    id: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Log
# ---------------------------------------------------------------------------
class LogBase(BaseModel):
    service: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    raw_context: Optional[str] = None


class LogOut(LogBase):
    id: str
    machine_id: str
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------
class IssueOut(BaseModel):
    id: str
    machine_id: str
    log_id: Optional[str] = None
    service: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    ai_raw_response: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IssueDetail(IssueOut):
    """Extended issue view with nested machine and log context."""
    machine: Optional[MachineOut] = None
    trigger_log: Optional[LogOut] = None
    commands: list["CommandOut"] = []


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------
class CommandOut(BaseModel):
    id: str
    issue_id: str
    machine_id: str
    command_text: str
    safe_to_auto_execute: bool
    approval_status: str
    approved_by: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
class ExecutionOut(BaseModel):
    id: str
    command_id: str
    status: str
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent inbound payloads
# ---------------------------------------------------------------------------
class AgentReportPayload(BaseModel):
    """Sent by client agent when it detects an error/warning."""
    hostname: str
    system_info: MachineBase
    service: Optional[str] = None
    severity: str = "error"
    trigger_message: str
    log_context: str = Field(description="Surrounding 100-200 log lines")


class AgentResultPayload(BaseModel):
    """Sent by client agent after executing a command."""
    command_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""


# ---------------------------------------------------------------------------
# AI analysis result
# ---------------------------------------------------------------------------
class AIAnalysisResult(BaseModel):
    severity: str = "medium"
    confidence: float = 0.5
    summary: str = ""
    root_cause: str = ""
    recommended_command: str = ""
    safe_to_auto_execute: bool = False


# Rebuild forward refs
IssueDetail.model_rebuild()
