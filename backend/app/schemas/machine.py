from typing import Optional, List
from typing_extensions import Literal

from pydantic import BaseModel

class MachineRegistration(BaseModel):
    hostname: str
    machine_name: Optional[str] = None
    hwid: str
    os: str
    arch: str
    ip_address: Optional[str] = None

class MachineRegistrationResponse(BaseModel):
    machine_id: str
    message: str
