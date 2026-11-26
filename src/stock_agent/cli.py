import argparse
import asyncio
import sys

from google.oauth2 import service_account
from pydantic import ValidationError
from pydantic_ai.exceptions import AgentRunError
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_core import ErrorDetails

from stock_agent.agent import Answer, agent
from stock_agent.settings import Settings


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
        result = asyncio.run(agent.run(args.question, model=build_model(settings)))
    except AgentRunError as error:
        print(f"stock-agent: the model request failed ({error}). Try again later.", file=sys.stderr)
        return 1
    print(render(result.output))
    return 0


def build_model(settings: Settings) -> GoogleModel:
    if settings.uses_google_cloud:
        credentials = service_account.Credentials.from_service_account_file(
            settings.google_application_credentials.expanduser()
        )
        provider = GoogleCloudProvider(
            credentials=credentials,
            project=credentials.project_id,
            location=settings.google_cloud_location,
        )
    else:
        provider = GoogleProvider(api_key=settings.google_api_key.get_secret_value())
    return GoogleModel(settings.gemini_model_name, provider=provider)


def _explain(problem: ErrorDetails) -> str:
    message = problem["msg"].removeprefix("Value error, ")
    # Cross-field checks have no single field, so their message names the variable itself.
    if not problem["loc"]:
        return message
    return f"{str(problem['loc'][0]).upper()}: {message}"
