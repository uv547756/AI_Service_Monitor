"""
Log monitor — watches journalctl output for errors and warnings.
"""
import logging
import re
import subprocess
import threading
from collections import deque
from typing import Callable, Optional

from config import AgentConfig

logger = logging.getLogger(__name__)


class LogMonitor:
    """
    Monitors journalctl logs in real-time, detects errors/warnings,
    and invokes a callback with the trigger line and surrounding context.
    """

    def __init__(self, on_error: Callable[[str, str, str, str], None]):
        """
        Args:
            on_error: callback(service, severity, trigger_message, log_context)
        """
        self.on_error = on_error
        self._buffer: deque = deque(maxlen=200)  # rolling log context
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Compile patterns
        self._error_re = re.compile(
            "|".join(AgentConfig.ERROR_PATTERNS), re.IGNORECASE
        )
        self._warning_re = re.compile(
            "|".join(AgentConfig.WARNING_PATTERNS), re.IGNORECASE
        )

    def start(self):
        """Start monitoring in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Log monitor started")

    def stop(self):
        """Stop the monitor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Log monitor stopped")

    def _monitor_loop(self):
        """Main loop — tails journalctl and checks each line."""
        cmd = ["journalctl", "-f", "--no-pager", "-o", "short-iso", "-q"]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            logger.error("journalctl not found — log monitoring disabled")
            return

        try:
            while self._running and proc.poll() is None:
                line = proc.stdout.readline()
                if not line:
                    continue

                line = line.strip()
                self._buffer.append(line)

                # Detect severity
                severity = self._classify_line(line)
                if severity:
                    service = self._extract_service(line)
                    context = "\n".join(self._buffer)
                    logger.info("Detected %s in %s: %s", severity, service, line[:120])
                    self.on_error(service, severity, line, context)
        finally:
            proc.terminate()
            proc.wait()

    def _classify_line(self, line: str) -> Optional[str]:
        """Returns 'error', 'warning', or None."""
        if self._error_re.search(line):
            return "error"
        if self._warning_re.search(line):
            return "warning"
        return None

    def _extract_service(self, line: str) -> str:
        """
        Try to extract the service/unit name from a journalctl line.
        Format: "2024-01-15T10:30:00+0000 hostname service[pid]: message"
        """
        try:
            parts = line.split()
            if len(parts) >= 3:
                svc = parts[2]
                # Remove PID bracket: "nginx[1234]:" → "nginx"
                svc = re.sub(r"\[\d+\]:?$", "", svc)
                return svc.rstrip(":")
        except Exception:
            pass
        return "unknown"
