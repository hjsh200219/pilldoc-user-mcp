# Tech Debt Tracker

## Active Debt

### TD-001: Synchronous HTTP in Async Context
- **Severity**: Medium
- **Location**: `src/pilldoc/api.py` (all API calls use `requests`)
- **Impact**: Blocks the asyncio event loop during API calls
- **Proposed Fix**: Migrate from `requests` to `httpx` with async client
- **Effort**: Medium (all API functions need async conversion)

### TD-002: No Connection Pooling
- **Severity**: Low
- **Location**: `src/pilldoc/api.py`
- **Impact**: Each API call creates a new HTTP connection (TCP handshake overhead)
- **Proposed Fix**: Use `httpx.AsyncClient` with connection pool or `requests.Session`
- **Effort**: Low (wrap existing calls in session context)

### TD-003: No Test Suite
- **Severity**: High
- **Location**: Project-wide
- **Impact**: No automated validation of tool behavior, schema validation, or error handling
- **Proposed Fix**: Add pytest with mocked API responses for each tool domain
- **Effort**: High (test infrastructure + per-tool test cases)
- **Dependencies**: requirements.txt has pytest commented out

### TD-004: No Rate Limiting
- **Severity**: Low
- **Location**: `src/pilldoc/api.py`
- **Impact**: No protection against flooding the EDB Admin API
- **Proposed Fix**: Add token bucket or sliding window rate limiter in API client
- **Effort**: Low

### TD-005: No Circuit Breaker
- **Severity**: Low
- **Location**: `src/pilldoc/api.py`
- **Impact**: Repeated failures to a down endpoint are not short-circuited
- **Proposed Fix**: Add circuit breaker pattern (closed/open/half-open states)
- **Effort**: Medium

### TD-006: In-Memory Token Only
- **Severity**: Low
- **Location**: `src/auth/manager.py`
- **Impact**: Token lost on server restart; requires re-authentication
- **Proposed Fix**: Optional encrypted token file cache (with TTL)
- **Effort**: Low

## Resolved Debt

_None yet._
