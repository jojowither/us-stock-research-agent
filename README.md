# US Stock Research Agent

An LLM agent that answers questions about US companies' reported financials, with every number traced back to the SEC Filing it came from.

Example (the answer's wording comes from the model and varies; the Sources lines are printed by the code):

```console
$ uv run stock-agent "What was Microsoft's revenue last year?"
Microsoft's revenue for Fiscal Year 2026 (period ended 2026-06-30) was US$331.8 billion.

Sources:
- MSFT revenue FY2026 (period ended 2026-06-30): 331,839,000,000 USD — 10-K filed 2026-07-29
```

It is a learning project built in thin end-to-end slices; see [docs/ROADMAP.md](docs/ROADMAP.md). It gives no investment advice.

## How it works

- **CLI** (`stock-agent`) takes one question, prints the answer and its Sources, and exits.
- **Agent** ([Pydantic AI](https://ai.pydantic.dev/) + Gemini) decides which Financial Facts to look up and writes the answer. An output validator rejects any Financial Fact the tool did not return.
- **MCP server** ([FastMCP](https://gofastmcp.com/)) runs as a separate process over stdio and owns data access. It exposes one tool, `get_financial_fact(ticker, metric, fiscal_year?)`. See [ADR 0001](docs/adr/0001-mcp-server-as-separate-process.md).

Slice 1 serves a fixed set of Financial Facts taken from SEC companyfacts: AAPL and MSFT, Revenue and Net Income, Fiscal Years 2025 and 2026. Domain terms are defined in [GLOSSARY.md](GLOSSARY.md).

## Install

Requires [uv](https://docs.astral.sh/uv/). uv installs the Python version in `.python-version` for you.

```bash
git clone https://github.com/jojowither/us-stock-research-agent.git
cd us-stock-research-agent
uv sync
```

## Configure

```bash
cp .env.example .env
```

Then pick one way to reach Gemini:

- **API key** (default): set `GOOGLE_API_KEY` to a key from [Google AI Studio](https://aistudio.google.com/apikey). `STOCK_AGENT_MODEL` (`google:<model>`) is optional.
- **Service account** (Vertex AI): set `STOCK_AGENT_MODEL=google-cloud:<model>` and `GOOGLE_APPLICATION_CREDENTIALS` to the key file's path. The Google Cloud project comes from the key file; `GOOGLE_CLOUD_LOCATION` defaults to `global`. Keep the key file outside the repository.

## Run

```bash
uv run stock-agent "蘋果 2025 財年的淨利是多少？"
```

The answer comes back in the question's language. If the data isn't available, the agent says so and lists what is.

## Develop

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests never call a real LLM and need no API key: the CLI test replaces only the model, and talks to the real MCP server process. CI runs the same three commands on every pull request.
