from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_name: str = "staleness-rag"
    log_level: str = "INFO"
    log_file: str = "logs/chronicle.log"

    openai_api_key: str
    model_name: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=_ENV_PATH)


settings = Settings()
