from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    opnsense_url: str = "https://192.168.1.1"
    opnsense_api_key: str = ""
    opnsense_api_secret: str = ""
    opnsense_verify_ssl: bool = False

    # Refresh interval in seconds
    refresh_interval: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
