from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints

# Every module speaks upper-case tickers; this type normalises input at each
# boundary so "aapl" from the LLM and "AAPL" in the data always match.
Ticker = Annotated[
    str,
    BeforeValidator(lambda v: v.strip().upper() if isinstance(v, str) else v),
    StringConstraints(pattern=r"^[A-Z][A-Z.\-]{0,9}$"),
]


class FinancialMetric(StrEnum):
    REVENUE = "revenue"
    NET_INCOME = "net_income"


class FinancialFact(BaseModel):
    """One reported value of a Financial Metric for a Company and Fiscal Year."""

    ticker: Ticker = Field(description="Company ticker in upper case, e.g. AAPL.")
    metric: FinancialMetric = Field(description="The Financial Metric this value measures.")
    fiscal_year: int = Field(description="The Company's own Fiscal Year, e.g. 2026.")
    period_end: date = Field(description="Last day of the period the value covers.")
    value: int = Field(description="Raw value in `unit`, not scaled (no thousands or millions).")
    unit: str = Field(description="Unit of `value`, e.g. USD.")
    filing: str = Field(
        description="The Filing the value was reported in, e.g. 10-K filed 2026-11-03."
    )
