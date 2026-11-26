import json
import sys

from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ToolReturnPart

from stock_agent.facts import GET_FINANCIAL_FACT_TOOL, FinancialFact

INSTRUCTIONS = f"""\
You answer questions about US companies' reported financials.

- Use only Financial Facts returned by the {GET_FINANCIAL_FACT_TOOL} tool; never answer from memory
  or estimate a value.
- Always state the Fiscal Year and its period end date for every value.
- Fiscal Year means the Company's own Fiscal Year. Read "last year" (or "去年") as the latest
  Fiscal Year the tool has; omit fiscal_year to get it, and say which Fiscal Year you used.
- Answer in the language of the question.
- Format values with currency and a readable scale, e.g. "US$478.8 billion" in English or
  "4,788 億美元" in Chinese.
- When the tool says data is unavailable, say so plainly, mention what the tool says is available,
  and leave `facts` empty for that request.
- Write tickers in upper case, e.g. AAPL.
- List every Financial Fact you used in `facts`, copied exactly from the tool results.
"""


class Answer(BaseModel):
    """The final answer to the question, with the Financial Facts it relied on."""

    text: str = Field(
        description=(
            "The answer to the question. State the Fiscal Year and period end of every "
            "value, and take every value from `facts`."
        )
    )
    facts: list[FinancialFact] = Field(
        description=(
            f"Every Financial Fact the answer relied on, copied exactly from "
            f"{GET_FINANCIAL_FACT_TOOL} results."
        )
    )


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
            f"These facts were not returned by {GET_FINANCIAL_FACT_TOOL} in this conversation: "
            f"{[fact.model_dump(mode='json') for fact in invented]}. "
            "Copy Financial Facts exactly from the tool results, or call the tool again."
        )
    return answer


def _facts_returned_by_tool(ctx: RunContext[None]) -> list[FinancialFact]:
    facts = []
    for message in ctx.messages:
        for part in message.parts:
            # A tool error (e.g. data not available) also arrives as a return part,
            # marked "retried" and carrying the error text instead of a Financial Fact.
            if (
                isinstance(part, ToolReturnPart)
                and part.tool_name == GET_FINANCIAL_FACT_TOOL
                and part.outcome == "success"
            ):
                content = part.content
                if isinstance(content, str):
                    content = json.loads(content)
                facts.append(FinancialFact.model_validate(content))
    return facts


agent = build_agent()
