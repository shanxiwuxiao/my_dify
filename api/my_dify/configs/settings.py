from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MY_DIFY_",
        env_file=".env",
        extra="ignore",
    )

    model_base_url: str = "https://api.openai.com/v1"
    model_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    model_timeout: float = 30.0

    database_url: str = "sqlite:///my_dify.db"
    secret_key: str = "development-only-change-me"
    session_cookie_secure: bool = False
    max_content_length: int = 2_000_000

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value
