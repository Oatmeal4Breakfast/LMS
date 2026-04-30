from enum import StrEnum, auto
from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvType(StrEnum):
    PRODUCTION = auto()
    DEVELOPMENT = auto()


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False, env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    db_uri: str = Field(validation_alias="DB_URI")
    env_type: EnvType = Field(validation_alias="ENV_TYPE")
    smtp_server: str = Field(validation_alias="SMTP_SERVER")
    smtp_from_email: EmailStr = Field(validation_alias="SMTP_FROM_EMAIL")
    smtp_password: str = Field(validation_alias="SMTP_PASSWORD")


class CSRFSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False, env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    secret_key: str = Field(validation_alias="CSRF_SECRET")
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_key: str = "csrf_token"
    token_key: str = "token_key"


def get_config() -> Config:
    return Config()
