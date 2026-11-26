import argparse
import asyncio
import sys

from pydantic import ValidationError
from pydantic_ai.exceptions import AgentRunError
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
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
    model = GoogleModel(
        settings.gemini_model_name,
        provider=GoogleProvider(api_key=settings.google_api_key.get_secret_value()),
    )
    try:
        result = asyncio.run(agent.run(args.question, model=model))
    except AgentRunError as error:
        print(f"stock-agent: the model request failed ({error}). Try again later.", file=sys.stderr)
        return 1
    print(render(result.output))
    return 0


def _explain(problem: ErrorDetails) -> str:
    field = str(problem["loc"][0]).upper()
    if problem["type"] == "missing":
        return f"{field} is not set. Copy .env.example to .env and fill it in."
    return f"{field}: {problem['msg'].removeprefix('Value error, ')}"
