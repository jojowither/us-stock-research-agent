# US Stock Research Agent

An agent that answers research questions about US-listed companies from their SEC filings, prices and news.

## Companies and periods

**Company**:
A US-listed issuer that files with the SEC, referred to by its ticker (e.g. AAPL).
_Avoid_: Stock, symbol, issuer

**Fiscal Year**:
The company's own reporting year, named as the company names it in its 10-K (Apple's FY2024 ended 2024-09-28). Never a calendar year unless the company's fiscal year happens to end in December.
_Avoid_: Year, calendar year, FY field

**Period End**:
The last day of the period a reported number covers. The reliable identifier for a period, since a filing's own year can differ from the period it reports.
_Avoid_: Filing date, report date

## Financial data

**Filing**:
A document a company submits to the SEC, such as a 10-K annual report.
_Avoid_: Report, statement, document

**Financial Fact**:
One reported value of a Financial Metric for a Company and Fiscal Year, together with its Period End and the Filing it came from.
_Avoid_: Data point, record, row, number

**Financial Metric**:
A named measure a company reports for a period, such as Revenue or Net Income.
_Avoid_: Number, figure, KPI, field

**Revenue**:
The company's total net sales for a period, as reported in its income statement.
_Avoid_: Sales, turnover, top line

**Net Income**:
Profit attributable to the company's shareholders for a period, after all expenses and taxes.
_Avoid_: Profit, earnings, bottom line
