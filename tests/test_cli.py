import json

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from stock_agent.agent import agent
from stock_agent.cli import main


def scripted_llm(tool_args: dict, answer_text: str) -> FunctionModel:
    """Stand-in LLM: call the data tool once, then answer with what it returned."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returns = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
        if not returns:
            return ModelResponse(parts=[ToolCallPart("get_financial_fact", tool_args)])
        fact = returns[0].content
        if isinstance(fact, str):
            fact = json.loads(fact)
        final = {"text": answer_text, "facts": [fact]}
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, final)])

    return FunctionModel(respond)


def test_cli_prints_answer_and_the_financial_fact_it_used(monkeypatch, capfd):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    llm = scripted_llm(
        {"ticker": "AAPL", "metric": "revenue"},
        "Apple's FY2026 revenue was US$478.8 billion (period ended 2026-09-26).",
    )

    with agent.override(model=llm):
        exit_code = main(["What was Apple's latest revenue?"])

    out = capfd.readouterr().out
    assert exit_code == 0
    assert "Apple's FY2026 revenue was US$478.8 billion" in out
    assert "AAPL revenue FY2026 (period ended 2026-09-26): 478,834,000,000 USD" in out
    assert "10-K filed 2026-11-03" in out


def test_cli_rejects_a_non_gemini_model_setting(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("STOCK_AGENT_MODEL", "openai:gpt-6")

    with pytest.raises(ValidationError, match="only Gemini models"):
        main(["What was Apple's latest revenue?"])


def _replace_the_real_fact(real: dict) -> list[dict]:
    return [{**real, "value": 999_000_000_000}]


def _add_an_invented_fact(real: dict) -> list[dict]:
    return [real, {**real, "ticker": "MSFT", "value": 999_000_000_000}]


@pytest.mark.parametrize("first_facts", [_replace_the_real_fact, _add_an_invented_fact])
def test_cli_never_prints_a_financial_fact_the_tool_did_not_return(monkeypatch, capfd, first_facts):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    real_fact: dict = {}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        last = messages[-1].parts
        output_tool = info.output_tools[0].name
        # The output validator's rejection comes back as the output tool's result.
        if any(
            isinstance(p, ToolReturnPart | RetryPromptPart) and p.tool_name == output_tool
            for p in last
        ):
            final = {"text": "Corrected answer.", "facts": [real_fact]}
            return ModelResponse(parts=[ToolCallPart(output_tool, final)])
        returns = [
            p for p in last if isinstance(p, ToolReturnPart) and p.tool_name == "get_financial_fact"
        ]
        if not returns:
            args = {"ticker": "AAPL", "metric": "revenue"}
            return ModelResponse(parts=[ToolCallPart("get_financial_fact", args)])
        content = returns[0].content
        real_fact.update(json.loads(content) if isinstance(content, str) else content)
        final = {"text": "Invented answer.", "facts": first_facts(real_fact)}
        return ModelResponse(parts=[ToolCallPart(output_tool, final)])

    with agent.override(model=FunctionModel(respond)):
        exit_code = main(["What was Apple's latest revenue?"])

    out = capfd.readouterr().out
    assert exit_code == 0
    assert "Corrected answer." in out
    assert "999,000,000,000" not in out
    assert "478,834,000,000 USD" in out
