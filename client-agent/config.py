"""
Client agent configuration.
"""


class AgentConfig:
    # Server connection
    SERVER_URL: str = "http://192.168.1.180:8000"
    API_KEY: str = "changeme-dev-key"

    # Monitoring
    POLL_INTERVAL: int = 5  # seconds between polling for commands
    LOG_CHECK_INTERVAL: int = 5  # seconds between log checks

    # journalctl filters
    MONITORED_SERVICES: list = [
        "nginx", "docker", "sshd", "postgresql", "mysql",
        "redis", "systemd", "kernel", "cron", "apache2",
    ]

    # Error detection patterns
    ERROR_PATTERNS: list = [
        r"error",
        r"failed",
        r"fatal",
        r"critical",
        r"exception",
        r"oom",
        r"killed",
        r"segfault",
        r"timeout",
        r"refused",
    ]

    WARNING_PATTERNS: list = [
        r"warning",
        r"warn",
        r"deprecated",
        r"retry",
        r"slow",
    ]

    # Command execution
    COMMAND_TIMEOUT: int = 120  # seconds
    BLOCKED_COMMANDS: list = [
        "rm -rf /",
        "mkfs",
        "dd if=",
        ":(){ :|:& };:",
    ]
