import argparse
import asyncio
import sys
from pathlib import Path

from google.auth.exceptions import GoogleAuthError
from google.oauth2 import service_account
from pydantic import ValidationError
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_core import ErrorDetails

from stock_agent.agent import Answer, agent
from stock_agent.settings import ApiKeyAuth, ServiceAccountAuth, Settings


def render(answer: Answer) -> str:
    if not answer.facts:
        return answer.text
    lines = [answer.text, "", "Sources:"]
    for fact in answer.facts:
        lines.append(
            f"- {fact.ticker} {fact.metric} FY{fact.fiscal_year} (period ended {fact.period_end}): "
            f"{fact.value:,} {fact.unit} — {fact.filing.form} filed {fact.filing.filed_on}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stock-agent", description="Ask about US companies' reported financials."
    )
    parser.add_argument("question")
    args = parser.parse_args(argv)

    try:
        settings = Settings()
    except ValidationError as error:
        for problem in error.errors():
            print(f"stock-agent: {_explain(problem)}", file=sys.stderr)
        return 2
    try:
        model = build_model(settings)
    except ValueError as error:
        print(f"stock-agent: {error}", file=sys.stderr)
        return 2
    try:
        result = asyncio.run(agent.run(args.question, model=model))
    except (AgentRunError, GoogleAuthError) as error:
        print(f"stock-agent: {_describe_model_failure(error)}", file=sys.stderr)
        return 1
    print(render(result.output))
    return 0


def build_model(settings: Settings) -> GoogleModel:
    match settings.auth:
        case ServiceAccountAuth(key_file=key_file, location=location):
            credentials = _load_service_account(key_file)
            provider = GoogleCloudProvider(
                credentials=credentials, project=credentials.project_id, location=location
            )
        case ApiKeyAuth(api_key=api_key):
            provider = GoogleProvider(api_key=api_key.get_secret_value())
    return GoogleModel(settings.gemini_model_name, provider=provider)


def _load_service_account(path: Path) -> service_account.Credentials:
    try:
        return service_account.Credentials.from_service_account_file(path)
    except ValueError as error:
        raise ValueError(
            f"GOOGLE_APPLICATION_CREDENTIALS: {path} is not a valid service account key "
            f"({_first_line(error)})"
        ) from error


def _describe_model_failure(error: AgentRunError | GoogleAuthError) -> str:
    if isinstance(error, GoogleAuthError):
        return f"authentication with the service account failed ({_first_line(error)})"
    if isinstance(error, UnexpectedModelBehavior):
        return f"the model did not produce a valid answer ({error.message})."
    if isinstance(error, ModelHTTPError):
        detail = f"HTTP {error.status_code}: {_provider_message(error.body)}"
    else:
        detail = error.message
    return f"the model request failed ({detail}). Try again later."


def _provider_message(body: object) -> str:
    # Gemini wraps errors as {"error": {"message": ...}}; the rest of the body is quota detail.
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        body = body["error"].get("message", body)
    return _first_line(body if body is not None else "")


def _first_line(text: object) -> str:
    lines = str(text).strip().splitlines()
    return lines[0] if lines else "no details"


def _explain(problem: ErrorDetails) -> str:
    message = problem["msg"].removeprefix("Value error, ")
    # Cross-field checks have no single field, so their message names the variable itself.
    if not problem["loc"]:
        return message
    return f"{str(problem['loc'][0]).upper()}: {message}"
