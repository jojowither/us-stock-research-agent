# Data access lives in a separate MCP server, not inside the agent

Financial data is exposed through an MCP server that runs as its own process; the agent reaches it as an MCP client (stdio locally, Streamable HTTP when deployed) rather than calling Python functions in-process. This keeps a hard boundary between data access and LLM reasoning, lets any MCP client (e.g. Claude Desktop) reuse the same tools, and means swapping the hard-coded fixture for SEC data or Postgres never touches the agent.

## Considered Options

- **Plain Pydantic AI tools in the agent process**: simpler and faster to test, but couples data access to one agent and skips the protocol boundary the project exists to exercise.

## Consequences

- The Financial Fact shape (and the Ticker and Financial Metric types inside it) is a deliberate shared contract: the server returns it and the agent's answer carries it. The agent imports the type, never the server's data access. Changing that shape is a contract change that touches both sides, and later any non-Python MCP client too.
