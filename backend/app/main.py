from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from datetime import datetime
import uuid

# Import Schemas
from backend.app.schemas.error import ErrorData
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.remote import HeartbeatRequest, HeartbeatResponse, Job, JobResult, JobType, FixResult

# Import Services
from backend.app.core.analyzer import ErrorAnalyzer
from backend.app.services.telegram_bot import telegram_service

# Data Stores and Helpers
from backend.app.core.state import (
    ANALYSIS_STORE, 
    MACHINE_STORE, 
    JOB_QUEUE, 
    JOB_RESULTS, 
    ERROR_MACHINE_MAP,
    APPROVAL_STATES,
    add_job
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await telegram_service.start()
    yield
    # Shutdown
    await telegram_service.stop()

app = FastAPI(lifespan=lifespan)
analyzer = ErrorAnalyzer()

@app.get("/")
async def root():
    return {"message": "AI Service Monitor Backend is running"}

# --- Error Reporting ---

@app.post("/api/v1/error")
async def report_error(error_data: ErrorData, background_tasks: BackgroundTasks):
    """
    Receives error from client, analyzes it, and sends approval request.
    """
    try:
        # Analyze
        print(f"Analyzing error: {error_data.error_id}")
        analysis_result = analyzer.analyze_and_fix(error_data)
        
        # Store result
        ANALYSIS_STORE[error_data.error_id] = analysis_result
        ERROR_MACHINE_MAP[error_data.error_id] = error_data.machine.machine_id
        
        # Send Notification (Background task to not block response)
        summary = f"Host: {error_data.machine.hostname}\nService: {error_data.error.service}\nDiagnosis: {analysis_result.diagnosis}\n\nProposed Fixes:"
        for i, cmd in enumerate(analysis_result.commands, 1):
            sudo_req = "Yes" if cmd.requires_sudo else "No"
            summary += f"\n\n{i}. Command: {cmd.command}"
            summary += f"\n   Reason: {cmd.explanation}"
            summary += f"\n   Risk: {cmd.risk_level.upper()}"
            summary += f"\n   Sudo: {sudo_req}"
            if cmd.confidence:
                summary += f"\n   Confidence: {cmd.confidence}"
        background_tasks.add_task(telegram_service.send_approval_request, error_data.error_id, summary)
        
        return {"status": "received", "error_id": error_data.error_id, "analysis": "pending_approval"}
    except Exception as e:
        print(f"Error processing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/command/{error_id}")
async def get_command(error_id: str):
    """
    Client polls this. Returns commands if approved.
    (Deprecated: Client should use Heartbeat Jobs)
    """
    status = APPROVAL_STATES.get(error_id, "unknown")
    
    # We force "pending" here to disable polling execution if the client is not yet updated?
    # Or we let it work for legacy?
    # Better to just return status so we don't crash.
    
    if status == "pending":
        return {"status": "pending"}
    elif status == "rejected":
        return {"status": "rejected"}
    elif status == "approved":
        result = ANALYSIS_STORE.get(error_id)
        if not result:
            return {"status": "error", "message": "Analysis not found"}
        
        return {
            "status": "approved",
            "diagnosis": result.diagnosis,
            "commands": result.commands,
            "verification": result.verification
        }
    else:
        return {"status": "unknown"}

# --- Remote Monitoring & Control ---

@app.post("/api/v1/heartbeat")
async def heartbeat(hb: HeartbeatRequest) -> HeartbeatResponse:
    """
    Client sends heartbeat. Server updates last seen and returns pending jobs.
    """
    MACHINE_STORE[hb.machine_id] = hb
    
    # Get pending jobs
    pending = JOB_QUEUE.get(hb.machine_id, [])
    # Clear queue after sending? 
    # Or wait for ack? For simplicity, we assume client receives them.
    # To be safer, client should ack, but let's clear for now to avoid loops.
    if pending:
        JOB_QUEUE[hb.machine_id] = []
        print(f"Sending {len(pending)} jobs to {hb.hostname}")
        
    return HeartbeatResponse(pending_jobs=pending)

@app.post("/api/v1/job_result")
async def job_result(result: JobResult):
    """
    Client reports job execution result.
    """
    JOB_RESULTS[result.job_id] = result
    print(f"Job {result.job_id} completed. Success: {result.success}")
    
    await telegram_service.notify_job_result(result)
    
    return {"status": "ack"}
@app.post("/api/v1/fix_result")
async def fix_result(result: FixResult):
    """
    Client reports results of specific fix execution chain.
    """
    print(f"Fix result for {result.error_id}: Success={result.success}")
    await telegram_service.notify_fix_result(result)
    return {"status": "ack"}


