from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "SafeFlow API"
    debug: bool = False
    version: str = "1.0.0"

    # Database settings
    database_url: str = "sqlite:///./safeflow.db"

    # Security settings
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30

    # API settings
    api_v1_prefix: str = "/api/v1"

    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"

        # Special handling for list field
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "cors_origins":
                return [x.strip() for x in raw_val.split(",")]
            return cls.json_loads(raw_val)


settings = Settings()
