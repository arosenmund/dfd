from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="Deepfake Detection API", env="APP_NAME")
    database_url: str = Field(default="sqlite:///./dfd.db", env="DATABASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""

    return Settings()


settings = get_settings()
