"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Central config — all values come from env vars or .env file."""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./logwatch.db"

    # API Security
    API_KEY: str = "changeme-dev-key"

    # AI Provider: "openai", "gemini", or "ollama"
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_MODE: str = "polling"  # "polling" or "webhook"
    TELEGRAM_WEBHOOK_URL: Optional[str] = None  # e.g. https://yourdomain.com/telegram/webhook

    # Command safety
    COMMAND_BLOCKLIST: str = "rm -rf /,mkfs,dd if=,:(){ :|:& };:"
    AUTO_EXECUTE_SAFE: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def blocked_commands(self) -> list[str]:
        return [c.strip() for c in self.COMMAND_BLOCKLIST.split(",") if c.strip()]


settings = Settings()
