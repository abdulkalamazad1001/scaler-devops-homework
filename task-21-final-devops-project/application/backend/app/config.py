from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables.

    In Kubernetes the non-secret values come from a ConfigMap and DB_USER /
    DB_PASSWORD come from a Secret. DATABASE_URL, when set, wins over the parts.
    """

    app_name: str = "TaskBoard API"
    app_version: str = "dev"
    app_env: str = "local"
    log_level: str = "INFO"
    create_tables_on_startup: bool = False

    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "taskboard"
    db_user: str = "taskboard"
    db_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()
