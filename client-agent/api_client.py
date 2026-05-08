"""
HTTP client for communicating with the LogWatch server.
"""
import logging
import time
from typing import Optional

import httpx

from config import AgentConfig

logger = logging.getLogger(__name__)


class APIClient:
    """Handles all communication with the central server."""

    def __init__(self):
        self.base_url = AgentConfig.SERVER_URL.rstrip("/")
        self.headers = {"X-API-Key": AgentConfig.API_KEY}
        self._client = httpx.Client(timeout=30, headers=self.headers)

    def report_error(
        self,
        hostname: str,
        system_info: dict,
        service: str,
        severity: str,
        trigger_message: str,
        log_context: str,
    ) -> Optional[dict]:
        """Send an error/warning report to the server."""
        payload = {
            "hostname": hostname,
            "system_info": system_info,
            "service": service,
            "severity": severity,
            "trigger_message": trigger_message,
            "log_context": log_context,
        }

        for attempt in range(3):
            try:
                resp = self._client.post(f"{self.base_url}/agent/report", json=payload)
                resp.raise_for_status()
                data = resp.json()
                logger.info("Report accepted — issue_id=%s", data.get("issue_id"))
                return data
            except httpx.HTTPError as e:
                logger.warning("Report attempt %d failed: %s", attempt + 1, e)
                time.sleep(2 ** attempt)

        logger.error("Failed to send report after 3 attempts")
        return None

    def get_pending_commands(self, machine_id: str) -> list[dict]:
        """Poll for commands that have been approved and are awaiting execution."""
        try:
            resp = self._client.get(f"{self.base_url}/agent/pending/{machine_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Failed to poll commands: %s", e)
            return []

    def send_result(
        self,
        command_id: str,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> bool:
        """Send command execution result back to the server."""
        payload = {
            "command_id": command_id,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }
        try:
            resp = self._client.post(f"{self.base_url}/agent/result", json=payload)
            resp.raise_for_status()
            logger.info("Result sent for command %s", command_id)
            return True
        except httpx.HTTPError as e:
            logger.error("Failed to send result: %s", e)
            return False

    def close(self):
        self._client.close()
