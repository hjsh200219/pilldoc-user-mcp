# Quality Standards: pilldoc-user-mcp

## Code Quality

### Validation
- All tool inputs pass through `utils/validation.py` with schema-based type coercion
- Pydantic models in `src/schemas/` enforce structure for auth, accounts, pharmacy, statistics
- Business number, email, phone formats validated and normalized before API calls
- Date ranges checked for logical consistency (start <= end, max span)

### Error Handling
- Custom exception hierarchy: `MCPError` > `ValidationError`, `AuthenticationError`, `NotFoundError`, `APIError`
- `@handle_error` decorator on tool handlers catches all exceptions and returns standardized error response
- Sensitive data (password, token) masked in logs via `_mask_sensitive_data()`
- All errors logged to stderr (required for stdio MCP protocol)

### Observability
- `@log_tool_call` decorator logs start/end of every tool invocation with duration
- `@track_execution` decorator records call count, success rate, min/max/avg latency per tool
- Global `Metrics` singleton exposes tool-level statistics
- `LogContext` manager for structured operation logging

## Testing Strategy

### Current State
- Test dependencies listed but commented out in `requirements.txt` (pytest, black, flake8, mypy)
- No test directory exists yet

### Recommended Plan
1. **Unit tests**: Validate `utils/validation.py` functions (type coercion, format checks)
2. **Schema tests**: Verify Pydantic models reject invalid data
3. **Tool tests**: Mock `requests` and test each tool's happy path + error handling
4. **Integration tests**: Test on-demand module loading (load/unload cycles)

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `snake_case.py` | `accounts_tools.py` |
| Classes | `PascalCase` | `AuthManager`, `BaseTool` |
| Functions | `snake_case` | `register_auth_tools()` |
| Tool names | `snake_case` (MCP) | `get_accounts`, `find_pharm` |
| Env vars | `UPPER_SNAKE` | `EDB_BASE_URL` |
| Schema models | `PascalCase` (Pydantic) | `AccountFilter`, `LoginRequest` |

## Performance Guidelines

- On-demand loading: modules load only on first tool call (controlled by `MCP_ON_DEMAND`)
- Default timeout: 15s for all API calls (configurable via `EDB_TIMEOUT`)
- Max retries: 3 (configurable in Settings)
- Pagination: default page_size=20, max=100
- Statistics tools use `summary_only` and `max_items` parameters to prevent oversized responses
