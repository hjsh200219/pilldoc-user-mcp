# Security

## Authentication & Authorization

### Token Management
- Tokens stored **in-memory only** (never written to disk by the server)
- Auto-login from env vars at startup (optional, fails gracefully)
- Per-tool fallback: tools accept explicit `token` or `userId/password` parameters
- Token refresh on 401 via re-login with stored credentials

### Credential Protection
- `EDB_USER_ID`, `EDB_PASSWORD` loaded from `.env.local` (gitignored)
- Passwords, tokens, API keys masked in all log output via `_mask_sensitive_data()`
- `.env`, `.env.*`, `CLAUDE.md` excluded in `.gitignore`

## Data Access Controls

### API Access
- All EDB Admin API calls require Bearer token authentication
- No direct database writes; mutations go through the EDB Admin API

### Database Access (PostgreSQL)
- National medical institutions: **SELECT-only** (write queries rejected at tool level)
- Query results limited by default (`limit=100`)
- **Parameterized queries** to prevent SQL injection
- Connection string in `DATABASE_URL` env var (not hardcoded)

## Sensitive Data Handling

### Log Sanitization
Fields containing these keywords are auto-masked: `password`, `token`, `api_key`, `secret`, `authorization`

```python
# Example: "Bearer eyJhbG..." -> "Bear****..."
_mask_sensitive_data({"token": "eyJhbGciOiJ..."})
```

### Response Sanitization
- Credentials never included in MCP tool responses
- Error responses use standardized format without leaking internals

## Network Security

- MCP protocol runs over **stdio** (no network listener)
- All EDB API calls use **HTTPS**
- Default timeout: 15 seconds per API call
- No rate limiting on the MCP server side (relies on upstream API limits)

## Known Security Considerations

1. **No token expiry tracking**: Server does not proactively refresh tokens before expiry
2. **No request signing**: API calls use Bearer token only (no HMAC or request signing)
3. **No audit log**: Tool call logs go to stderr but are not persisted
4. **No IP restriction**: MCP server accepts connections from any stdio client
5. **Custom SQL queries**: `execute_institutions_query` accepts user SQL (SELECT-only enforced, but complex injection vectors should be reviewed)
