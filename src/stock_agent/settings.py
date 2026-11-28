from dataclasses import dataclass
from pathlib import Path

from pydantic import PrivateAttr, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GOOGLE_PROVIDER_PREFIX = "google:"
GOOGLE_CLOUD_PROVIDER_PREFIX = "google-cloud:"


@dataclass(frozen=True)
class ApiKeyAuth:
    """Reach Gemini through the Gemini API with a Google AI Studio key."""

    api_key: SecretStr


@dataclass(frozen=True)
class ServiceAccountAuth:
    """Reach Gemini through Vertex AI with a service account key file."""

    key_file: Path
    location: str


type Auth = ApiKeyAuth | ServiceAccountAuth


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    stock_agent_model: str = "google:gemini-3.8-flash"
    google_api_key: SecretStr | None = None
    google_application_credentials: Path | None = None
    google_cloud_location: str = "global"

    _auth: Auth = PrivateAttr()

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
        self._auth = self._resolve_auth()
        return self

    def _resolve_auth(self) -> Auth:
        if self.stock_agent_model.startswith(GOOGLE_CLOUD_PROVIDER_PREFIX):
            path = self.google_application_credentials
            if path is None:
                raise _missing("GOOGLE_APPLICATION_CREDENTIALS")
            if not path.expanduser().is_file():
                raise ValueError(
                    f"GOOGLE_APPLICATION_CREDENTIALS: no service account key file at {path}"
                )
            return ServiceAccountAuth(
                key_file=path.expanduser(), location=self.google_cloud_location
            )
        if self.google_api_key is None:
            raise _missing("GOOGLE_API_KEY")
        return ApiKeyAuth(api_key=self.google_api_key)

    @property
    def auth(self) -> Auth:
        """The credentials the model's provider needs; validation guarantees one is set."""
        return self._auth

    @property
    def gemini_model_name(self) -> str:
        return self.stock_agent_model.split(":", 1)[1]


def _missing(variable: str) -> ValueError:
    return ValueError(f"{variable} is not set. Copy .env.example to .env and fill it in.")
