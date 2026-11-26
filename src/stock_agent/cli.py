import argparse
import asyncio

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from stock_agent.agent import Answer, agent
from stock_agent.settings import Settings


def render(answer: Answer) -> str:
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

    settings = Settings()
    model = GoogleModel(
        settings.gemini_model_name,
        provider=GoogleProvider(api_key=settings.google_api_key.get_secret_value()),
    )
    result = asyncio.run(agent.run(args.question, model=model))
    print(render(result.output))
    return 0
