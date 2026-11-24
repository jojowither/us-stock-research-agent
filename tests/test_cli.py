import json

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from stock_agent.agent import agent
from stock_agent.cli import main


def scripted_llm(tool_args: dict, answer_text: str) -> FunctionModel:
    """Stand-in LLM: call the data tool once, then answer with what it returned."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returns = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
        if not returns:
            return ModelResponse(parts=[ToolCallPart("get_financial_metric", tool_args)])
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
