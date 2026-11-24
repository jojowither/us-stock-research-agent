import sys

from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

from stock_agent.facts import FinancialFact

INSTRUCTIONS = """\
You answer questions about US companies' reported financials.
Use only numbers returned by the get_financial_metric tool; never answer from memory.
Always state the Fiscal Year and its period end date.
List every Financial Fact you used in `facts`.
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
    return Agent(None, output_type=Answer, toolsets=[data_server], instructions=INSTRUCTIONS)


agent = build_agent()
