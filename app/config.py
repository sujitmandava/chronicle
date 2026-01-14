from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_name: str = "staleness-rag"
    log_level: str = "INFO"
    log_file: str = "logs/chronicle.log"
    db_path: str = "data/chronicle.db"
    staleness_half_life_days: float = 30.0
    staleness_warning_days: int = 30
    staleness_max_age_days: int = 180

    openai_api_key: str
    model_name: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=_ENV_PATH)


settings = Settings()
