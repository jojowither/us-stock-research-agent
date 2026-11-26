import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from stock_agent.agent import agent
from stock_agent.cli import build_model, main
from stock_agent.facts import GET_FINANCIAL_FACT_TOOL
from stock_agent.settings import Settings


def scripted_llm(tool_args: dict, answer_text: str) -> FunctionModel:
    """Stand-in LLM: call the data tool once, then answer with what it returned."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returns = [p for p in messages[-1].parts if isinstance(p, ToolReturnPart)]
        if not returns:
            return ModelResponse(parts=[ToolCallPart(GET_FINANCIAL_FACT_TOOL, tool_args)])
        fact = returns[0].content
        if isinstance(fact, str):
            fact = json.loads(fact)
        final = {"text": answer_text, "facts": [fact]}
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, final)])

    return FunctionModel(respond)


def test_cli_prints_answer_and_the_financial_fact_it_used(monkeypatch, capfd):
    """FunctionModel drives the real MCP server over stdio; the Pydantic AI docs don't say so."""
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


def _llm_that_must_not_be_called() -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise AssertionError("the CLI called the model despite invalid settings")

    return FunctionModel(respond)


def test_cli_fails_fast_with_a_clear_message_when_the_api_key_is_missing(capfd):
    with agent.override(model=_llm_that_must_not_be_called()):
        exit_code = main(["What was Apple's latest revenue?"])

    err = capfd.readouterr().err
    assert exit_code == 2
    assert "GOOGLE_API_KEY is not set" in err
    assert "Traceback" not in err


def test_cli_rejects_a_non_gemini_model_setting(monkeypatch, capfd):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("STOCK_AGENT_MODEL", "openai:gpt-6")

    with agent.override(model=_llm_that_must_not_be_called()):
        exit_code = main(["What was Apple's latest revenue?"])

    err = capfd.readouterr().err
    assert exit_code == 2
    assert "only Gemini models are supported" in err


def _replace_the_real_fact(real: dict) -> list[dict]:
    return [{**real, "value": 999_000_000_000}]


def _add_an_invented_fact(real: dict) -> list[dict]:
    return [real, {**real, "ticker": "MSFT", "value": 999_000_000_000}]


@pytest.mark.parametrize("first_answer_facts", [_replace_the_real_fact, _add_an_invented_fact])
def test_cli_never_prints_a_financial_fact_the_tool_did_not_return(
    monkeypatch, capfd, first_answer_facts
):
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
            p
            for p in last
            if isinstance(p, ToolReturnPart) and p.tool_name == GET_FINANCIAL_FACT_TOOL
        ]
        if not returns:
            args = {"ticker": "AAPL", "metric": "revenue"}
            return ModelResponse(parts=[ToolCallPart(GET_FINANCIAL_FACT_TOOL, args)])
        content = returns[0].content
        real_fact.update(json.loads(content) if isinstance(content, str) else content)
        final = {"text": "Invented answer.", "facts": first_answer_facts(real_fact)}
        return ModelResponse(parts=[ToolCallPart(output_tool, final)])

    with agent.override(model=FunctionModel(respond)):
        exit_code = main(["What was Apple's latest revenue?"])

    out = capfd.readouterr().out
    assert exit_code == 0
    assert "Corrected answer." in out
    assert "999,000,000,000" not in out
    assert "478,834,000,000 USD" in out


def test_cli_says_plainly_when_data_is_unavailable(monkeypatch, capfd):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    seen_errors: list[str] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # A tool error comes back as a tool return marked "retried", carrying the error text.
        errors = [
            p
            for p in messages[-1].parts
            if isinstance(p, ToolReturnPart) and p.outcome == "retried"
        ]
        if not errors:
            args = {"ticker": "TSLA", "metric": "revenue"}
            return ModelResponse(parts=[ToolCallPart(GET_FINANCIAL_FACT_TOOL, args)])
        seen_errors.append(errors[0].content)
        final = {"text": "No revenue data for TSLA. Available: AAPL, MSFT.", "facts": []}
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, final)])

    with agent.override(model=FunctionModel(respond)):
        exit_code = main(["What was Tesla's latest revenue?"])

    out = capfd.readouterr().out
    assert exit_code == 0
    assert "AAPL (fiscal years 2025, 2026)" in seen_errors[0]
    assert "No revenue data for TSLA" in out
    assert "Sources:" not in out


def test_cli_prints_a_readable_error_when_the_llm_call_fails(monkeypatch, capfd):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def rate_limited(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise ModelHTTPError(status_code=429, model_name="gemini-3.8-flash", body="quota")

    with agent.override(model=FunctionModel(rate_limited)):
        exit_code = main(["What was Apple's latest revenue?"])

    err = capfd.readouterr().err
    assert exit_code == 1
    assert "stock-agent: the model request failed" in err
    assert "429" in err
    assert "Traceback" not in err


def test_cli_answers_after_several_unavailable_lookups(monkeypatch, capfd):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    unknown = ["TSLA", "NVDA", "AMZN"]

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if unknown:
            args = {"ticker": unknown.pop(0), "metric": "revenue"}
            return ModelResponse(parts=[ToolCallPart(GET_FINANCIAL_FACT_TOOL, args)])
        final = {"text": "No revenue data for TSLA, NVDA or AMZN.", "facts": []}
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, final)])

    with agent.override(model=FunctionModel(respond)):
        exit_code = main(["Compare Tesla, Nvidia and Amazon revenue."])

    assert exit_code == 0
    assert "No revenue data for TSLA, NVDA or AMZN." in capfd.readouterr().out


@pytest.fixture
def service_account_file(tmp_path):
    """A well-formed service account key that no real Google Cloud project knows."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    path = tmp_path / "service-account.json"
    path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "test-project",
                "private_key_id": "test",
                "private_key": pem,
                "client_email": "agent@test-project.iam.gserviceaccount.com",
                "client_id": "1",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
    )
    return path


def test_cli_answers_with_a_service_account_and_no_api_key(
    monkeypatch, capfd, service_account_file
):
    monkeypatch.setenv("STOCK_AGENT_MODEL", "google-cloud:gemini-3.6-flash")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(service_account_file))
    llm = scripted_llm({"ticker": "AAPL", "metric": "revenue"}, "Apple's FY2026 revenue.")

    with agent.override(model=llm):
        exit_code = main(["What was Apple's latest revenue?"])

    assert exit_code == 0
    assert "Apple's FY2026 revenue." in capfd.readouterr().out


def test_google_cloud_model_authenticates_with_the_service_account(
    monkeypatch, service_account_file
):
    monkeypatch.setenv("STOCK_AGENT_MODEL", "google-cloud:gemini-3.6-flash")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(service_account_file))

    model = build_model(Settings())

    assert model.system == "google-cloud"
    assert model.model_name == "gemini-3.6-flash"


def test_google_model_authenticates_with_the_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    model = build_model(Settings())

    assert model.system == "google"


@pytest.mark.parametrize(
    ("credentials", "expected"),
    [
        (None, "GOOGLE_APPLICATION_CREDENTIALS is not set"),
        ("missing.json", "GOOGLE_APPLICATION_CREDENTIALS: no service account key file at"),
    ],
)
def test_cli_explains_a_missing_service_account_key(monkeypatch, capfd, credentials, expected):
    monkeypatch.setenv("STOCK_AGENT_MODEL", "google-cloud:gemini-3.6-flash")
    if credentials is not None:
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", credentials)

    with agent.override(model=_llm_that_must_not_be_called()):
        exit_code = main(["What was Apple's latest revenue?"])

    err = capfd.readouterr().err
    assert exit_code == 2
    assert expected in err
    assert "Traceback" not in err
