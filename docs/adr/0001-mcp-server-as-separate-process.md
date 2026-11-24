# Data access lives in a separate MCP server, not inside the agent

Financial data is exposed through an MCP server that runs as its own process; the agent reaches it as an MCP client (stdio locally, Streamable HTTP when deployed) rather than calling Python functions in-process. This keeps a hard boundary between data access and LLM reasoning, lets any MCP client (e.g. Claude Desktop) reuse the same tools, and means swapping the hard-coded fixture for SEC data or Postgres never touches the agent.

## Considered Options

- **Plain Pydantic AI tools in the agent process**: simpler and faster to test, but couples data access to one agent and skips the protocol boundary the project exists to exercise.
