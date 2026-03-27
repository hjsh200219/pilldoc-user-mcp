# Reliability: pilldoc-user-mcp

## Error Boundaries

### Layer-wise Error Handling

| Layer | Strategy | Recovery |
|-------|----------|----------|
| MCP Protocol | Handled by MCP SDK | Auto-reconnect via stdio |
| Tool Execution | `@handle_error` decorator | Returns `{success: false, error: {...}}` |
| API Calls | `requests.raise_for_status()` | Caught by tool-level error handler |
| Auth | Token refresh on 401 | Re-login with stored credentials |
| Database | psycopg2 exception handling | Connection retry, SELECT-only enforcement |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR | AUTH_ERROR | NOT_FOUND | API_ERROR | INTERNAL_ERROR",
    "message": "Human-readable description",
    "details": {}
  }
}
```

## Auth Resilience

- Auto-login at server startup (fails gracefully with warning)
- Every tool can accept explicit `token` or `userId/password` as fallback
- Token stored in memory only (never written to disk by server)

## API Call Safety

### Content-Type Auto-Retry
`update_account` tries multiple Content-Type headers on 415 errors:
1. `application/json; charset=utf-8`
2. `application/json`
3. `application/merge-patch+json`
4. `application/x-www-form-urlencoded`
5. `multipart/form-data`

Non-415 errors fail immediately (no unnecessary retries).

### Field Auto-Mapping
Update tools auto-convert common field name mistakes:
- `ownerName` / `약국장` -> `displayName`
- `isAdDisplay` -> `약국광고표기` (with value conversion: 0->"표시", 1->"미표시")
- `phone` / `전화번호` -> `약국전화번호`

## Database Safety

- National medical institutions queries: **SELECT-only** (write queries rejected)
- Query results limited by default (`limit=100`)
- Parameterized queries to prevent SQL injection

## Sensitive Data Protection

- Passwords, tokens, API keys masked in all log output
- `.env`, `.env.local` files in `.gitignore`
- CLAUDE.md excluded from git (in `.gitignore`)
- Credentials never included in tool responses

## Known Limitations

1. **No connection pooling**: Each API call creates a new HTTP connection via `requests`
2. **Synchronous HTTP in async context**: `requests` library is blocking; runs in asyncio but blocks the event loop during API calls
3. **In-memory token only**: Token lost on server restart; auto-login re-authenticates
4. **No rate limiting**: Relies on upstream API rate limits
5. **No circuit breaker**: Repeated failures to an endpoint are not short-circuited
