# Design Overview

> Canonical design reference for pilldoc-user-mcp.

## Architecture Pattern

**Client-Server via MCP Protocol (stdio)**

```
MCP Client (Claude Desktop / IDE Agent)
  |  JSON-RPC over stdio
  v
FastMCP Server (mcp_server.py)
  |  On-demand module loading
  v
Tool Registry (mcp_tools/)
  |  Auth + API + Validation glue
  v
Business Logic (pilldoc/api.py)
  |  HTTP requests (synchronous)
  v
External APIs (EDB Admin API) + PostgreSQL (salesdb)
```

## Key Design Decisions

### 1. Dual Entry Points
- **FastMCP** (`mcp_server.py`): Primary entry with on-demand lazy loading
- **Standard SDK** (`server.py`): Handler-based approach for explicit initialization
- Rationale: FastMCP provides simpler tool registration; Standard SDK gives more control

### 2. On-Demand Module Loading
- Tools grouped into modules: `auth`, `pilldoc_service`, `medical_institution`, `product_orders`, `national_medical_institutions`
- Modules load only on first tool call via `__import__` + lambda loaders
- Reduces startup time from loading 8+ tool modules to loading 0
- Controlled by `MCP_ON_DEMAND` env var (default: `true`)

### 3. Content-Type Auto-Retry
- `update_account` tries 5 Content-Type variants on 415 errors
- Non-415 errors fail immediately (no wasted retries)
- Handles EDB API inconsistencies transparently

### 4. Field Auto-Mapping
- Common Korean/English field name variants auto-converted
- Value normalization (e.g., `isAdDisplay: 0` -> `"표시"`)
- Reduces user error without losing flexibility

### 5. System Prompt as MCP Prompt
- Tool usage guidelines registered as `tool_usage_guide` MCP prompt
- Helps AI agents select the correct tool for ambiguous queries
- Distinguishes "national medical institutions" vs "PillDoc subscribers"

## Layer Map

See [docs/design-docs/layer-rules.md](design-docs/layer-rules.md) for the full dependency rules.

| Layer | Directory | May Import From |
|-------|-----------|----------------|
| Entry | `mcp_server.py`, `server.py` | handlers, auth, utils, mcp_tools |
| Handlers | `handlers/` | mcp_tools |
| Tool Registration | `mcp_tools/` | pilldoc, auth, utils, schemas, tools/base |
| Schemas | `schemas/` | (none from src) |
| Business Logic | `pilldoc/` | utils |
| Auth | `auth/` | utils |
| Utils | `utils/`, `tools/base.py` | (none from src) |

## Related Docs

- [Core Beliefs](design-docs/core-beliefs.md)
- [Layer Rules](design-docs/layer-rules.md)
- [Architecture](ARCHITECTURE.md)
