import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/app_db",
    )
    ECHO_DB: bool = False


settings = Settings()