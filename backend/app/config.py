from anyio.functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MACHINE_TOKEN_EXPIRE_DAYS: int = 365

    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "AI Monitoring System"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()