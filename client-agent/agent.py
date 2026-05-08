"""
LogWatch Client Agent — main entry point.

Monitors journalctl logs, reports errors to the central server,
polls for approved commands, executes them, and reports results.
"""
import logging
import os
import signal
import sys
import time
import threading

from config import AgentConfig
from system_info import get_system_info
from log_monitor import LogMonitor
from api_client import APIClient
from executor import execute as execute_command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("logwatch-agent")


class Agent:
    """Main agent orchestrator."""

    def __init__(self):
        self.api = APIClient()
        self.system_info = get_system_info()
        self.hostname = self.system_info["hostname"]
        self.machine_id = None  # Set after first report
        self._running = False
        self._report_lock = threading.Lock()
        self._last_report_time = 0
        self._min_report_interval = 10  # debounce: min seconds between reports

    def start(self):
        """Start the agent."""
        logger.info("=" * 60)
        logger.info("LogWatch Agent starting on %s", self.hostname)
        logger.info("Server: %s", AgentConfig.SERVER_URL)
        logger.info("=" * 60)

        self._running = True

        # Start log monitor
        self.monitor = LogMonitor(on_error=self._on_error_detected)
        self.monitor.start()

        # Start command polling loop
        self._poll_commands()

    def stop(self):
        """Gracefully stop the agent."""
        logger.info("Shutting down agent...")
        self._running = False
        self.monitor.stop()
        self.api.close()

    def _on_error_detected(self, service: str, severity: str, trigger: str, context: str):
        """Callback from LogMonitor when an error/warning is detected."""
        # Debounce rapid-fire errors
        now = time.time()
        with self._report_lock:
            if now - self._last_report_time < self._min_report_interval:
                logger.debug("Debouncing error report")
                return
            self._last_report_time = now

        # Refresh system info periodically
        self.system_info = get_system_info()

        result = self.api.report_error(
            hostname=self.hostname,
            system_info=self.system_info,
            service=service,
            severity=severity,
            trigger_message=trigger,
            log_context=context,
        )

        if result:
            # Store machine_id so we can poll for approved commands
            if result.get("machine_id") and not self.machine_id:
                self.machine_id = result["machine_id"]
                logger.info("Machine registered with id: %s", self.machine_id)
            logger.info("First report sent successfully")

    def _poll_commands(self):
        """Main polling loop — checks for approved commands and executes them."""
        while self._running:
            try:
                if self.machine_id:
                    commands = self.api.get_pending_commands(self.machine_id)
                    if commands:
                        logger.info("Found %d pending command(s)", len(commands))
                    for cmd in commands:
                        logger.info("Executing approved command: %s", cmd["command_text"])
                        exit_code, stdout, stderr = execute_command(cmd["command_text"])
                        logger.info("Command finished — exit_code=%d", exit_code)
                        self.api.send_result(
                            command_id=cmd["id"],
                            exit_code=exit_code,
                            stdout=stdout,
                            stderr=stderr,
                        )
                else:
                    logger.debug("No machine_id yet — waiting for first report")
            except Exception as e:
                logger.error("Polling error: %s", e)

            time.sleep(AgentConfig.POLL_INTERVAL)


def main():
    agent = Agent()

    def signal_handler(sig, frame):
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    main()
