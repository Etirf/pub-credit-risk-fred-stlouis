from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with PostgreSQL defaults.
    
    PostgreSQL configuration:
    - Username: postgres
    - Password: postgres (change in production!)
    - Database: credit_risk
    - Host: localhost (or postgres in Docker)
    - Port: 5432
    
    These are created automatically by docker-compose.yml.
    """
    fred_api_key: str | None = None
    database_url: str = "postgresql://postgres:postgres@localhost:5432/credit_risk"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
    )


settings = Settings()
