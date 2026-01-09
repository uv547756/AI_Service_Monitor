from fastapi import APIRouter
from backend.app.schemas.machine import MachineRegistration
from backend.app.services.machine_service import register_machine

router = APIRouter(prefix="/machines", tags=["machines"])

@router.post("/register")
def register(data: MachineRegistration):
    return register_machine(data)