# Architecture: pilldoc-user-mcp

## System Overview

PillDoc User MCP is a local MCP (Model Context Protocol) server that provides pharmacy account management, user info lookup, campaign management, medical institution data, and product order tools for MCP-compatible clients (Claude Desktop, IDE agents, etc.).

**Runtime**: Python 3.9+ | **Protocol**: MCP over stdio | **Framework**: FastMCP (primary), Standard MCP SDK (alternate)

## Data Flow

```
Claude Desktop / MCP Client
  |  (stdio, JSON-RPC)
  v
FastMCP Server (mcp_server.py)        Standard MCP Server (server.py)
  |                                      |
  v                                      v
On-Demand Module Loader              Handler Layer (handlers/)
  |                                      |
  v                                      v
MCP Tool Registry (mcp_tools/)       MCP Tool Registry (mcp_tools/)
  |                                      |
  v                                      v
Business Logic (pilldoc/api.py)      Business Logic (pilldoc/api.py)
  |                                      |
  v                                      v
External APIs (EDB Admin API)        External APIs (EDB Admin API)
  + PostgreSQL (salesdb)               + PostgreSQL (salesdb)
```

## Layer Map

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **Entry** | `src/mcp_server.py` | FastMCP server creation, on-demand module loading, system prompt |
| **Entry (alt)** | `src/server.py` | Standard MCP SDK server with handler-based architecture |
| **Handlers** | `src/handlers/` | MCP protocol request routing (tools, resources, prompts) |
| **Tool Registration** | `src/mcp_tools/` | MCP tool definitions and registration per domain |
| **Schemas** | `src/schemas/` | Pydantic models for request/response validation |
| **Business Logic** | `src/pilldoc/` | API client for EDB Admin API calls |
| **Auth** | `src/auth/` | Login flow, token management, AuthManager |
| **Utils** | `src/utils/` | Config, errors, logging, metrics, validation |
| **Tools Base** | `src/tools/` | Abstract BaseTool class, ToolRegistry, decorators |
| **Config** | `src/config.py` | Pydantic Settings (env-based configuration) |

## Key Design Decisions

### 1. Dual Entry Points
- `mcp_server.py` (FastMCP): Primary entry, supports on-demand lazy loading via `MCP_ON_DEMAND` env var
- `server.py` (Standard SDK): Handler-based approach with explicit initialization

### 2. On-Demand Module Loading
Tools are grouped into modules (`auth`, `pilldoc_service`, `medical_institution`, `product_orders`, `national_medical_institutions`). Modules load only when their tools are first called, reducing startup time.

### 3. Auth Flow
- Environment-based auto-login on server start (optional)
- Token stored in AuthManager singleton
- Per-tool fallback: tools accept explicit `token` or `userId/password` parameters

### 4. Content-Type Auto-Retry
`update_account` automatically retries PATCH requests with different Content-Types (JSON, merge-patch, form-data) on 415 errors.

## External Dependencies

| Dependency | Purpose |
|------------|---------|
| `mcp>=1.14.0` | MCP SDK + FastMCP |
| `requests` | HTTP client for EDB API |
| `pydantic` / `pydantic-settings` | Config validation, schema models |
| `python-dotenv` | .env file loading |
| `psycopg2-binary` | PostgreSQL connection (institutions DB) |

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `EDB_BASE_URL` | Yes | EDB Admin API base URL |
| `EDB_LOGIN_URL` | No | Override login endpoint |
| `EDB_USER_ID` | No | Default login user |
| `EDB_PASSWORD` | No | Default login password |
| `EDB_FORCE_LOGIN` | No | Force re-login (default: false) |
| `MCP_ON_DEMAND` | No | Enable lazy module loading (default: true) |
| `DATABASE_URL` | No | PostgreSQL connection for institutions |
