from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TrueData Market Monitor"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    truedata_username: str = ""
    truedata_password: str = ""

    database_url: str = ""

    # SmartTheta / local market API
    smarttheta_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
