from typing import List

from pydantic import BaseModel, Field
from typing_extensions import Literal
from datetime import datetime

from backend.app.schemas.error import MachineContext


class MachineRegistrationRequest(BaseModel):
    hostname: str
    machine_name: str
    hwid: str

    os: str
    arch: Literal["x86_64", "arm64", "aarch64"]

    services: List[str] = Field(..., examples=["nginx", "postgresql"])
    ip_addr: str

class ErrorCreate(BaseModel):
    machine_id: str
    error_log: str
    detected_at: datetime
    severity: Literal["unknown", "critical", "error"]
    machine_context: MachineContext
# class MachineContext(BaseModel):
#     hostname: str
#     os: str
#     services: List[str]
#
#
# class ErrorData(BaseModel):
#     machine_id: str
#     error_log: str
#     detected_at: datetime
#     severity: str = "unknown"
#     machine_context: MachineContext