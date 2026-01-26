from typing import Dict, List, Set, Any
import uuid

from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.remote import HeartbeatRequest, Job, JobResult, JobType

# -- Data Stores --

# error_id -> AnalysisResult
ANALYSIS_STORE: Dict[str, AnalysisResult] = {}

# machine_id -> Last Heartbeat Data
MACHINE_STORE: Dict[str, HeartbeatRequest] = {}

# machine_id -> List[Job]
JOB_QUEUE: Dict[str, List[Job]] = {}

# job_id -> JobResult
JOB_RESULTS: Dict[str, JobResult] = {}

# Machine ID -> Set of Chat IDs
LINK_STORE: Dict[str, Set[int]] = {}

# Error ID -> Approval Status ("approved", "rejected", "pending") 
APPROVAL_STATES: Dict[str, str] = {}

# Error ID -> Machine ID lookup for execution
ERROR_MACHINE_MAP: Dict[str, str] = {}


# -- Helpers --

def add_job(machine_id: str, job_type: JobType, args: Dict[str, Any] = {}) -> str:
    if machine_id not in MACHINE_STORE:
        raise ValueError("Machine not found/active")
        
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    job = Job(job_id=job_id, type=job_type, args=args)
    
    if machine_id not in JOB_QUEUE:
        JOB_QUEUE[machine_id] = []
    JOB_QUEUE[machine_id].append(job)
    return job_id
