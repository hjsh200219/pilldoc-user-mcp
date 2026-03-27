# Frontend

> Not applicable to this project.

pilldoc-user-mcp is a backend MCP server with no frontend UI. It communicates exclusively via the MCP protocol (JSON-RPC over stdio) with MCP-compatible clients such as:

- **Claude Desktop** - Primary client
- **IDE Agents** - Claude Code, Cursor, etc.
- **Custom MCP Clients** - Any client implementing the MCP protocol

## Client Configuration

See the root `README.md` for Claude Desktop configuration examples (development and production server setups).

## MCP Protocol Interface

The server exposes:
- **Tools**: 25+ tools across 8 domains (auth, accounts, pharmacy, campaign, statistics, medical institution, orders, national institutions)
- **Prompts**: `tool_usage_guide` - AI agent guidance for tool selection
- **Resources**: None currently registered
