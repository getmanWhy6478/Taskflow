from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./taskmanager.db"
    secret_key: str = Field(default="bla-bla-bla-bla-goofy-key", min_length=10)
    postgres_user: str = "postgres"
    postgres_password: str = "PASSWORD"
    postgres_db: str = "taskflow"
    debug: bool = False


settings = Settings()
