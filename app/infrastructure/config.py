import logging
from pathlib import Path

from pydantic.functional_validators import field_validator
from pydantic.main import BaseModel
from pydantic_settings.main import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent


class DatabaseConnectionSettings(BaseModel):
    database_user: str
    database_name: str
    database_password: str
    database_host: str
    database_port: int


class CommonSettings(BaseModel):
    log_level: int

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, value: str) -> int:
        try:
            return logging.getLevelNamesMapping()[value]
        except KeyError as error:
            raise ValueError(f"Logging level with name {value} is not found in {logging!r} module") from error


class Settings(BaseSettings):
    # certs: CryptoSettings
    db_connection: DatabaseConnectionSettings
    common: CommonSettings
    model_config = SettingsConfigDict(env_file=(".env",), env_nested_delimiter="__", str_to_lower=True)
