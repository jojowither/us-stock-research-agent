from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GEMINI_PREFIX = "google:"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: SecretStr
    stock_agent_model: str = "google:gemini-3.8-flash"

    @field_validator("stock_agent_model")
    @classmethod
    def must_be_gemini(cls, value: str) -> str:
        if not value.startswith(GEMINI_PREFIX):
            raise ValueError(
                f"only Gemini models are supported; use '{GEMINI_PREFIX}<model>', got {value!r}"
            )
        return value

    @property
    def gemini_model_name(self) -> str:
        return self.stock_agent_model.removeprefix(GEMINI_PREFIX)
