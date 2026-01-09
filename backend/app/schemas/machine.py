from typing import Optional, List
from typing_extensions import Literal

from pydantic import BaseModel

class MachineRegistrationResponse(BaseModel):
    machine_id: str
    message: str

