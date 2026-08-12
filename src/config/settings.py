from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ShopWise Agent API"
    app_version: str = "v1"
    debug: bool = False
    api_prefix: str = "/api/v1"


settings = Settings()