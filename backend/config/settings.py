"""
Application configuration management.

Loads settings from environment variables with .env file support.
All configuration is centralized here to follow the 12-factor app principle.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        app_name: Human-readable name of the application.
        app_version: Semantic version string.
        debug: Enables verbose debug logging when True.
        host: Interface address the Uvicorn server binds to.
        port: TCP port the Uvicorn server listens on.
        aws_region: AWS region where the Bedrock Knowledge Base is hosted.
        knowledge_base_id: Amazon Bedrock Knowledge Base identifier.
        bedrock_model_arn: Foundation model ARN used for response generation.
        log_level: Standard Python logging level name.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "AWS DevOps Knowledge Assistant"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- AWS ---
    aws_region: str = "us-east-1"
    knowledge_base_id: str = "VVVEU6TPPM"
    bedrock_model_arn: str = (
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    )

    # --- Logging ---
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Using lru_cache ensures the .env file is parsed only once per process
    lifetime, making repeated calls effectively free.

    Returns:
        Settings: The fully populated settings instance.
    """
    return Settings()