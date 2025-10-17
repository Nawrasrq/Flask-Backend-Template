"""
Application configuration using Pydantic Settings.

This module defines the Settings class which loads configuration from
environment variables and provides type-safe access to application settings.
"""

from typing import List

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are type-checked and validated using Pydantic.
    Sensitive values use SecretStr to prevent accidental logging.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Flask Settings
    APP_NAME: str = Field(default="Flask Backend Template")
    FLASK_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: SecretStr = Field(
        default=SecretStr("dev-secret-key-change-in-production")
    )

    # Database Settings
    DATABASE_URL: str = Field(default="sqlite:///app.db")

    # JWT Settings
    JWT_SECRET_KEY: SecretStr = Field(
        default=SecretStr("jwt-secret-key-change-in-production")
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # Argon2 Settings
    ARGON2_TIME_COST: int = Field(default=2, ge=1)
    ARGON2_MEMORY_COST: int = Field(default=65536, ge=1024)
    ARGON2_PARALLELISM: int = Field(default=2, ge=1)

    # Encryption Settings
    ENCRYPTION_KEY: SecretStr = Field(
        default=SecretStr("encryption-key-change-in-production-must-be-32-bytes")
    )

    # Password Settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=6)

    # CORS Settings
    CORS_ORIGINS: str = Field(default="*")

    def get_cors_origins(self) -> List[str]:
        """
        Parse CORS origins from comma-separated string to list.

        Returns
        -------
        List[str]
            List of CORS origins
        """
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Caching Settings
    CACHE_TYPE: str = Field(default="simple")
    CACHE_DEFAULT_TIMEOUT: int = Field(default=300, ge=0)

    # Testing Settings
    TESTING: bool = Field(default=False)

    # API Documentation Settings
    API_TITLE: str = Field(default="Flask Backend Template API")
    API_VERSION: str = Field(default="1.0.0")
    OPENAPI_VERSION: str = Field(default="3.0.3")
    OPENAPI_URL_PREFIX: str = Field(default="/api/docs")
    OPENAPI_SWAGGER_UI_PATH: str = Field(default="/swagger")
    OPENAPI_SWAGGER_UI_URL: str = Field(
        default="https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )


# Singleton settings instance
settings = Settings()
