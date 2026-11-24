from datetime import date
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from stock_agent.facts import FinancialFact, Metric

mcp = FastMCP("stock-data")

# Values from SEC companyfacts, matched to each 10-K by period end rather than
# the `fy` field, which is the filing's year, not the period's.
FACTS = [
    FinancialFact(
        ticker="AAPL",
        metric=Metric.REVENUE,
        fiscal_year=2026,
        period_end=date(2026, 9, 26),
        value=478_834_000_000,
        unit="USD",
        source="10-K filed 2026-11-03",
    ),
]


@mcp.tool
def get_financial_metric(
    ticker: Annotated[str, Field(description="Company ticker in upper case, e.g. AAPL or MSFT.")],
    metric: Annotated[Metric, Field(description="Which Financial Metric to look up.")],
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

    Returns the exact reported value with its Fiscal Year, period end and source
    Filing. Use the returned numbers as-is; never estimate a value the tool did
    not return.
    """
    matches = [f for f in FACTS if f.ticker == ticker and f.metric == metric]
    if fiscal_year is not None:
        matches = [f for f in matches if f.fiscal_year == fiscal_year]
    if not matches:
        raise ToolError(f"No {metric} data for {ticker} fiscal year {fiscal_year}.")
    return max(matches, key=lambda f: f.fiscal_year)


if __name__ == "__main__":
    mcp.run(show_banner=False)
