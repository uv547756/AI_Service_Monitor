import httpx
import asyncio
from typing import Optional, Dict, Any, List
from client.agent.schemas import ErrorData, AnalysisResult, HeartbeatRequest, HeartbeatResponse, Job, JobResult

class ErrorSender:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_error(self, error_data: ErrorData) -> Optional[str]:
        """
        Sends error to backend. Returns error_id if successful.
        """
        try:
            payload = error_data.model_dump(mode='json')
            response = await self.client.post(f"{self.backend_url}/api/v1/error", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("error_id")
        except Exception as e:
            print(f"Failed to send error: {e}")
            return None

    async def check_command(self, error_id: str) -> tuple[str, Optional[AnalysisResult]]:
        """
        Polls for command. Returns (status, AnalysisResult) tuple.
        """
        try:
            response = await self.client.get(f"{self.backend_url}/api/v1/command/{error_id}")
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            if status == "approved":
                return status, AnalysisResult.model_validate(data)
            elif status == "rejected":
                # print(f"Fix for {error_id} was REJECTED.")
                return status, None
            else:
                # Pending or unknown
                return status, None
        except Exception as e:
            print(f"Failed to check command: {e}")
            return "error", None

    async def send_heartbeat(self, hb: HeartbeatRequest) -> List[Job]:
        """
        Sends heartbeat, returns list of pending jobs.
        """
        try:
            payload = hb.model_dump(mode='json')
            response = await self.client.post(f"{self.backend_url}/api/v1/heartbeat", json=payload)
            response.raise_for_status()
            data = response.json()
            hb_resp = HeartbeatResponse.model_validate(data)
            return hb_resp.pending_jobs
        except Exception as e:
            # print(f"Heartbeat failed: {e}")
            return []

    async def send_job_result(self, result: JobResult) -> bool:
        try:
            payload = result.model_dump(mode='json')
            response = await self.client.post(f"{self.backend_url}/api/v1/job_result", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send job result: {e}")
            return False

    async def send_fix_result(self, error_id: str, success: bool, log: str) -> bool:
        """
        Sends result of fix execution (approved command chain).
        Reuse JobResult or separate endpoint? 
        Reusing JobResult minimal payload structure:
        We need machine_id... simpler to make a new endpoint or flexible payload.
        Let's perform a simple POST to /api/v1/fix_result
        """
        try:
            payload = {
                "error_id": error_id,
                "success": success,
                "log": log
            }
            response = await self.client.post(f"{self.backend_url}/api/v1/fix_result", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send fix result: {e}")
            return False

    async def close(self):
        await self.client.aclose()
