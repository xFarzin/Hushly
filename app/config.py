from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    bot_token: str = "DEFAULT_TOKEN_CHANGE_ME"
    database_url: str = "sqlite+aiosqlite:///./hushly.db"
    web_base_url: str = "http://localhost:8000"

    # Security
    secret_key: str = "super_secret_key_change_me_in_production"
    algorithm: str = "HS256"

    # Rate Limiting (per minute)
    message_rate_limit: int = 5
    report_rate_limit: int = 3
    link_creation_limit: int = 10
    reaction_rate_limit: int = 10

    # App Settings
    max_message_length: int = 1000
    max_links_per_user: int = 20
    max_quick_replies: int = 10

    # Admins (Telegram IDs)
    super_admins: List[int] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
