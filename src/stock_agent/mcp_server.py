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

REVENUE, NET_INCOME = FinancialMetric.REVENUE, FinancialMetric.NET_INCOME


def _from_10k(
    ticker: str,
    metric: FinancialMetric,
    fiscal_year: int,
    period_end: date,
    value: int,
    filed_on: date,
) -> FinancialFact:
    return FinancialFact(
        ticker=ticker,
        metric=metric,
        fiscal_year=fiscal_year,
        period_end=period_end,
        value=value,
        unit="USD",
        filing=Filing(form="10-K", filed_on=filed_on),
    )


# Values from SEC companyfacts, matched to each 10-K by period end rather than
# the `fy` field, which is the filing's year, not the period's. Each FY2025 value
# is restated identically in the FY2026 10-K.
FACTS = [
    _from_10k("AAPL", REVENUE, 2026, date(2026, 9, 26), 478_834_000_000, date(2026, 11, 3)),
    _from_10k("AAPL", REVENUE, 2025, date(2025, 9, 27), 416_161_000_000, date(2025, 10, 31)),
    _from_10k("AAPL", NET_INCOME, 2026, date(2026, 9, 26), 132_175_000_000, date(2026, 11, 3)),
    _from_10k("AAPL", NET_INCOME, 2025, date(2025, 9, 27), 112_010_000_000, date(2025, 10, 31)),
    _from_10k("MSFT", REVENUE, 2026, date(2026, 6, 30), 331_839_000_000, date(2026, 7, 29)),
    _from_10k("MSFT", REVENUE, 2025, date(2025, 6, 30), 281_724_000_000, date(2025, 7, 30)),
    _from_10k("MSFT", NET_INCOME, 2026, date(2026, 6, 30), 133_749_000_000, date(2026, 7, 29)),
    _from_10k("MSFT", NET_INCOME, 2025, date(2025, 6, 30), 101_832_000_000, date(2025, 7, 30)),
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
        raise ToolError(
            f"No {metric} Financial Fact for {ticker} in {period}. "
            f"Available {metric}: {_available(ticker, metric)}."
        )
    return max(matches, key=lambda fact: fact.fiscal_year)


def _available(ticker: str, metric: FinancialMetric) -> str:
    """Fiscal years per ticker for `metric`, narrowed to `ticker` when it has any."""
    years: dict[str, list[int]] = {}
    for fact in sorted(FACTS, key=lambda fact: (fact.ticker, fact.fiscal_year)):
        if fact.metric == metric:
            years.setdefault(fact.ticker, []).append(fact.fiscal_year)
    if ticker in years:
        years = {ticker: years[ticker]}
    return ", ".join(f"{t} (fiscal years {', '.join(map(str, fys))})" for t, fys in years.items())


if __name__ == "__main__":
    mcp.run(show_banner=False)
