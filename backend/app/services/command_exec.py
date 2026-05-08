"""
Command execution service — safety validation and dispatch helpers.
"""
import logging

from ..security import is_command_safe

logger = logging.getLogger(__name__)


def validate_command(command_text: str) -> tuple[bool, str]:
    """
    Validate a command before approving execution.

    Returns (is_safe, reason).
    """
    if not command_text or not command_text.strip():
        return False, "Empty command"

    if not is_command_safe(command_text):
        return False, "Command matches blocklist"

    # Additional heuristic checks
    dangerous_patterns = [
        "chmod 777",
        "> /dev/sda",
        "wget|curl.*|.*sh",
        "eval ",
        "exec ",
    ]
    cmd_lower = command_text.lower()
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return False, f"Potentially dangerous pattern: {pattern}"

    return True, "OK"
