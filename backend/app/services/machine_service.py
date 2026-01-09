from backend.app.schemas.machine import MachineRegistration
import uuid

def register_machine(data: MachineRegistration) -> dict:
    return {
        "machine_id": str(uuid.uuid4()),
        "message": "Machine registered successfully",
    }