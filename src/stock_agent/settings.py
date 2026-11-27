from pathlib import Path

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GOOGLE_PROVIDER_PREFIX = "google:"
GOOGLE_CLOUD_PROVIDER_PREFIX = "google-cloud:"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stock_agent_model: str = "google:gemini-3.8-flash"
    google_api_key: SecretStr | None = None
    google_application_credentials: Path | None = None
    google_cloud_location: str = "global"

    @field_validator("stock_agent_model")
    @classmethod
    def must_be_gemini(cls, value: str) -> str:
        if not value.startswith((GOOGLE_PROVIDER_PREFIX, GOOGLE_CLOUD_PROVIDER_PREFIX)):
            raise ValueError(
                "only Gemini models are supported; use "
                f"'{GOOGLE_PROVIDER_PREFIX}<model>' (API key) or "
                f"'{GOOGLE_CLOUD_PROVIDER_PREFIX}<model>' (service account), got {value!r}"
            )
        return value

    @model_validator(mode="after")
    def must_have_credentials_for_the_provider(self) -> Settings:
        if self.uses_google_cloud:
            path = self.google_application_credentials
            if path is None:
                raise _missing("GOOGLE_APPLICATION_CREDENTIALS")
            if not path.expanduser().is_file():
                raise ValueError(
                    f"GOOGLE_APPLICATION_CREDENTIALS: no service account key file at {path}"
                )
        elif self.google_api_key is None:
            raise _missing("GOOGLE_API_KEY")
        return self

    @property
    def uses_google_cloud(self) -> bool:
        return self.stock_agent_model.startswith(GOOGLE_CLOUD_PROVIDER_PREFIX)

    @property
    def gemini_model_name(self) -> str:
        return self.stock_agent_model.split(":", 1)[1]


def _missing(variable: str) -> ValueError:
    return ValueError(f"{variable} is not set. Copy .env.example to .env and fill it in.")
