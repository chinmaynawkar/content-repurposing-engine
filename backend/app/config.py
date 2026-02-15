"""Application configuration loaded from environment variables.
This module loads important app settings from .env file using Pydantic.
All sensitive info (like API keys) should be set as environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Twelve-Factor config: all values from env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL


# Create a global settings object to be imported elsewhere in the app
settings = Settings()
