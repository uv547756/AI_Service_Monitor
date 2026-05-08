"""
Safe command executor — runs approved commands with safety checks.
"""
import logging
import subprocess

from config import AgentConfig

logger = logging.getLogger(__name__)


def is_safe(command: str) -> bool:
    """Check command against blocklist."""
    cmd_lower = command.lower().strip()
    for blocked in AgentConfig.BLOCKED_COMMANDS:
        if blocked.lower() in cmd_lower:
            logger.warning("Blocked dangerous command: %s", command)
            return False
    return True


def execute(command: str) -> tuple[int, str, str]:
    """
    Execute a shell command safely with timeout.

    Returns (exit_code, stdout, stderr).
    """
    if not is_safe(command):
        return -1, "", "Command blocked by safety policy"

    logger.info("Executing command: %s", command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=AgentConfig.COMMAND_TIMEOUT,
        )
        logger.info("Command finished — exit_code=%d", result.returncode)
        return result.returncode, result.stdout[-4096:], result.stderr[-4096:]

    except subprocess.TimeoutExpired:
        logger.error("Command timed out after %ds", AgentConfig.COMMAND_TIMEOUT)
        return -2, "", f"Command timed out after {AgentConfig.COMMAND_TIMEOUT}s"

    except Exception as e:
        logger.error("Command execution error: %s", e)
        return -3, "", str(e)
