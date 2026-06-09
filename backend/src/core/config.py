from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    # DB — the +asyncpg prefix tells SQLAlchemy to use the async driver
    database_url: str = "postgresql+asyncpg://worktalk:worktalk@localhost:5432/worktalk"

    # JWT — must be 32+ random bytes in production
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 10080  # 7 days


settings = Settings()
