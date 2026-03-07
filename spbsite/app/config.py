from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://spbsite:password@localhost:5432/spbsite"
    catalog_database_url: str = "sqlite+aiosqlite:///./spb_messages.db"

    # App
    secret_key: str = "change-me-to-a-random-secret-key"
    app_title: str = "SPBSite"

    # SPB domain constants
    ispb_local: str = "36266751"
    ispb_bacen: str = "00038166"
    ispb_selic: str = "00038121"

    # MQ queue name prefix
    mq_queue_prefix: str = "QR.REQ"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
