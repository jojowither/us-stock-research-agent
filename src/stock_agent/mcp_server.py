from datetime import date
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from stock_agent.facts import (
    GET_FINANCIAL_FACT_TOOL,
    Filing,
    FinancialFact,
    FinancialMetric,
    Ticker,
)

mcp = FastMCP("stock-data")

# Values from SEC companyfacts, matched to each 10-K by period end rather than
# the `fy` field, which is the filing's year, not the period's.
FACTS = [
    FinancialFact(
        ticker="AAPL",
        metric=FinancialMetric.REVENUE,
        fiscal_year=2026,
        period_end=date(2026, 9, 26),
        value=478_834_000_000,
        unit="USD",
        filing=Filing(form="10-K", filed_on=date(2026, 11, 3)),
    ),
]


@mcp.tool(name=GET_FINANCIAL_FACT_TOOL)
def get_financial_fact(
    ticker: Annotated[Ticker, Field(description="Company ticker, e.g. AAPL or MSFT.")],
    metric: Annotated[FinancialMetric, Field(description="Which Financial Metric to look up.")],
    fiscal_year: Annotated[
        int | None,
        Field(
            description=(
                "The Company's own Fiscal Year, e.g. 2026. Omit it to get the latest "
                "available Fiscal Year."
            )
        ),
    ] = None,
) -> FinancialFact:
    """Look up one Financial Fact a Company reported in its 10-K.

    Returns the exact reported value with its Fiscal Year, period end and the
    Filing it came from. Use the returned value as-is; never estimate a value the
    tool did not return.
    """
    matches = [fact for fact in FACTS if fact.ticker == ticker and fact.metric == metric]
    if fiscal_year is not None:
        matches = [fact for fact in matches if fact.fiscal_year == fiscal_year]
    if not matches:
        period = f"fiscal year {fiscal_year}" if fiscal_year is not None else "any fiscal year"
        raise ToolError(f"No {metric} Financial Fact for {ticker} in {period}.")
    return max(matches, key=lambda fact: fact.fiscal_year)


if __name__ == "__main__":
    mcp.run(show_banner=False)
