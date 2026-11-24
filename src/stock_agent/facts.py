from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class Metric(StrEnum):
    REVENUE = "revenue"
    NET_INCOME = "net_income"


class FinancialFact(BaseModel):
    """One reported value of a Financial Metric for a Company and Fiscal Year."""

    ticker: str = Field(description="Company ticker, e.g. AAPL.")
    metric: Metric = Field(description="The Financial Metric this value measures.")
    fiscal_year: int = Field(description="The Company's own Fiscal Year, e.g. 2026.")
    period_end: date = Field(description="Last day of the period the value covers.")
    value: int = Field(description="Raw value in `unit`, not scaled (no thousands or millions).")
    unit: str = Field(description="Unit of `value`, e.g. USD.")
    source: str = Field(description="The Filing the value was reported in.")
