from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class MachineContext(BaseModel):
    hostname: str
    os: str
    services: List[str]
    arch: Optional[str] = None
    kernel_version: Optional[str] = None

class ErrorData(BaseModel):
    machine_id: str
    error_log: str
    detected_at = datetime
    severity: Optional[str] = Field(
        default="unknown")
    machine_context: MachineContext