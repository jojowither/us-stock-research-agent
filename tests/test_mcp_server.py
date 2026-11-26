import pytest
from fastmcp import Client

from stock_agent.mcp_server import mcp

pytestmark = pytest.mark.anyio


async def test_returns_apple_revenue_for_requested_fiscal_year():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_fact",
            {"ticker": "AAPL", "metric": "revenue", "fiscal_year": 2026},
        )

    assert result.structured_content == {
        "ticker": "AAPL",
        "metric": "revenue",
        "fiscal_year": 2026,
        "period_end": "2026-09-26",
        "value": 478834000000,
        "unit": "USD",
        "filing": {"form": "10-K", "filed_on": "2026-11-03"},
    }


async def test_omitting_fiscal_year_returns_latest():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_fact", {"ticker": "AAPL", "metric": "revenue"}
        )

    assert result.structured_content["fiscal_year"] == 2026
    assert result.structured_content["value"] == 478834000000


async def test_lowercase_ticker_is_normalised_to_upper_case():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_fact", {"ticker": " aapl ", "metric": "revenue"}
        )

    assert result.structured_content["ticker"] == "AAPL"
