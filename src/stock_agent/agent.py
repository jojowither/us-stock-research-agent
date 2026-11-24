import json
import sys

from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ToolReturnPart

from stock_agent.facts import FinancialFact

INSTRUCTIONS = """\
You answer questions about US companies' reported financials.
Use only numbers returned by the get_financial_fact tool; never answer from memory.
Always state the Fiscal Year and its period end date.
Write tickers in upper case, e.g. AAPL.
List every Financial Fact you used in `facts`, copied exactly from the tool results.
"""


class Answer(BaseModel):
    text: str = Field(description="The answer to the question.")
    facts: list[FinancialFact] = Field(description="Financial Facts the answer relied on.")


def build_agent() -> Agent[None, Answer]:
    data_server = MCPToolset(
        StdioTransport(command=sys.executable, args=["-m", "stock_agent.mcp_server"])
    )
    # No model here: the CLI picks it from settings at run time, so importing
    # this module never needs an API key.
    agent = Agent(None, output_type=Answer, toolsets=[data_server], instructions=INSTRUCTIONS)
    agent.output_validator(facts_must_come_from_tool)
    return agent


def facts_must_come_from_tool(ctx: RunContext[None], answer: Answer) -> Answer:
    returned = _facts_returned_by_tool(ctx)
    invented = [fact for fact in answer.facts if fact not in returned]
    if invented:
        raise ModelRetry(
            "These facts were not returned by get_financial_fact in this conversation: "
            f"{[fact.model_dump(mode='json') for fact in invented]}. "
            "Copy Financial Facts exactly from the tool results, or call the tool again."
        )
    return answer


def _facts_returned_by_tool(ctx: RunContext[None]) -> list[FinancialFact]:
    facts = []
    for message in ctx.messages:
        for part in message.parts:
            if isinstance(part, ToolReturnPart) and part.tool_name == "get_financial_fact":
                content = part.content
                if isinstance(content, str):
                    content = json.loads(content)
                facts.append(FinancialFact.model_validate(content))
    return facts


agent = build_agent()
