from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HH WhatsApp Bot"
    app_base_url: str = "http://localhost:8000"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    hh_vacancy_id: str = ""
    hh_api_base_url: str = "https://api.hh.kz"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
