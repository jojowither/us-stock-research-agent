import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from stock_agent.mcp_server import mcp

pytestmark = pytest.mark.anyio


# Expected values come from SEC companyfacts for each 10-K, matched by period end.
FACTS_FROM_10K = [
    ("AAPL", "revenue", 2026, "2026-09-26", 478_834_000_000, "2026-11-03"),
    ("AAPL", "revenue", 2025, "2025-09-27", 416_161_000_000, "2025-10-31"),
    ("AAPL", "net_income", 2026, "2026-09-26", 132_175_000_000, "2026-11-03"),
    ("AAPL", "net_income", 2025, "2025-09-27", 112_010_000_000, "2025-10-31"),
    ("MSFT", "revenue", 2026, "2026-06-30", 331_839_000_000, "2026-07-29"),
    ("MSFT", "revenue", 2025, "2025-06-30", 281_724_000_000, "2025-07-30"),
    ("MSFT", "net_income", 2026, "2026-06-30", 133_749_000_000, "2026-07-29"),
    ("MSFT", "net_income", 2025, "2025-06-30", 101_832_000_000, "2025-07-30"),
]


@pytest.mark.parametrize(
    ("ticker", "metric", "fiscal_year", "period_end", "value", "filed_on"), FACTS_FROM_10K
)
async def test_returns_each_financial_fact_from_the_10k(
    ticker, metric, fiscal_year, period_end, value, filed_on
):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_fact",
            {"ticker": ticker, "metric": metric, "fiscal_year": fiscal_year},
        )

    assert result.structured_content == {
        "ticker": ticker,
        "metric": metric,
        "fiscal_year": fiscal_year,
        "period_end": period_end,
        "value": value,
        "unit": "USD",
        "filing": {"form": "10-K", "filed_on": filed_on},
    }


@pytest.mark.parametrize(
    ("ticker", "metric", "value"),
    [("AAPL", "revenue", 478_834_000_000), ("MSFT", "net_income", 133_749_000_000)],
)
async def test_omitting_fiscal_year_returns_latest(ticker, metric, value):
    async with Client(mcp) as client:
        result = await client.call_tool("get_financial_fact", {"ticker": ticker, "metric": metric})

    assert result.structured_content["fiscal_year"] == 2026
    assert result.structured_content["value"] == value


async def test_lowercase_ticker_is_normalised_to_upper_case():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_fact", {"ticker": " aapl ", "metric": "revenue"}
        )

    assert result.structured_content["ticker"] == "AAPL"


async def test_unknown_ticker_lists_available_tickers_and_fiscal_years():
    async with Client(mcp) as client:
        with pytest.raises(ToolError) as error:
            await client.call_tool("get_financial_fact", {"ticker": "TSLA", "metric": "revenue"})

    assert str(error.value) == (
        "No revenue Financial Fact for TSLA in any fiscal year. "
        "Available revenue: AAPL (fiscal years 2025, 2026), MSFT (fiscal years 2025, 2026)."
    )


async def test_unavailable_fiscal_year_lists_that_companys_fiscal_years():
    async with Client(mcp) as client:
        with pytest.raises(ToolError) as error:
            await client.call_tool(
                "get_financial_fact",
                {"ticker": "MSFT", "metric": "net_income", "fiscal_year": 2020},
            )

    assert str(error.value) == (
        "No net_income Financial Fact for MSFT in fiscal year 2020. "
        "Available net_income: MSFT (fiscal years 2025, 2026)."
    )


async def test_unsupported_financial_metric_is_rejected():
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Input should be 'revenue' or 'net_income'"):
            await client.call_tool("get_financial_fact", {"ticker": "AAPL", "metric": "ebitda"})
