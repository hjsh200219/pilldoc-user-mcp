# Core Beliefs

## 1. MCP as Integration Layer

PillDoc User MCP exists as a **bridge** between AI agents (Claude Desktop, IDE agents) and the EDB Admin API. The MCP protocol is the contract; the server is the translator.

## 2. On-Demand over Eager

Modules load only when their tools are first called. Startup cost stays constant regardless of how many tool domains exist. This is critical because MCP servers run as child processes with limited lifecycle control.

## 3. Auth is a Concern, Not a Layer

Authentication is handled transparently: auto-login from env vars on startup, per-tool fallback with explicit credentials, and token refresh on 401. Tool authors should never worry about auth state.

## 4. Downward-Only Dependencies

Imports flow strictly downward through the layer hierarchy (Entry > Handlers > mcp_tools > schemas/pilldoc/auth > utils). This prevents circular dependencies and keeps each layer testable in isolation.

## 5. Schemas are Contracts, Not Logic

Pydantic models in `src/schemas/` define shape and validation. They contain zero business logic, zero API calls, zero side effects. This makes them safe to import from any layer.

## 6. Field Auto-Mapping over Error Messages

When users pass common field name variants (Korean/English, camelCase/snake_case), the system auto-maps them to the correct API field rather than returning a validation error. Forgiveness over strictness.

## 7. SELECT-Only for Direct DB Access

Any tool that directly queries PostgreSQL (national medical institutions) enforces read-only access. Write operations go through the EDB Admin API, which owns the business rules.

## 8. Stdio Protocol Constraints Shape Everything

MCP over stdio means: logs go to stderr, responses go to stdout, no interactive prompts, no background threads for UI. Every design decision respects this constraint.
