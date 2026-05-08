"""
Security utilities: API key verification, command safety checks.
"""
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """FastAPI dependency — validates the X-API-Key header."""
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


def is_command_safe(command: str) -> bool:
    """
    Check if a command is safe to execute.
    Returns False if the command matches any entry in the blocklist.
    """
    cmd_lower = command.lower().strip()
    for blocked in settings.blocked_commands:
        if blocked.lower() in cmd_lower:
            return False
    return True
