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

    class Config:
        env_file = ".env"


settings = Settings()