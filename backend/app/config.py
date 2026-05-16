from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://localhost/sicbo"

    # JWT
    jwt_secret_key: str = "change-me-in-production-64chars"
    jwt_refresh_secret_key: str = "change-me-refresh-in-production-64chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Telegram
    telegram_bot_token: str = ""
    telegram_admin_ids: str = ""  # comma-separated
    telegram_admin_chat_id: str = ""

    # SePay
    sepay_webhook_secret: str = ""

    # Bank
    bank_account_no: str = ""
    bank_account_name: str = ""
    bank_name: str = "VietinBank"
    momo_phone: str = ""

    # XSMB - xosonhanh.vn API (500 req/day/IP, no auth)
    xsmb_api_latest: str = "https://xosonhanh.vn/wp-json/xosonhanh/v1/latest/MB"
    xsmb_api_history: str = "https://xosonhanh.vn/wp-json/xosonhanh/v1/history"

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    # Comma-separated list các origin được phép CORS (bổ sung cho frontend_url, ví dụ Vercel preview)
    cors_extra_origins: str = ""
    debug: bool = False

    @property
    def allowed_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.cors_extra_origins:
            origins.extend(o.strip() for o in self.cors_extra_origins.split(",") if o.strip())
        return origins

    @property
    def admin_telegram_ids(self) -> list[int]:
        if not self.telegram_admin_ids:
            return []
        return [int(x.strip()) for x in self.telegram_admin_ids.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
