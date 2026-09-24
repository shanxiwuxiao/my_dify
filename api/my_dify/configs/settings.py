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