from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database (PostgreSQL only) - single database for all tables
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/banuxSPB"

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
