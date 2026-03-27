# Plans

## Active

_No active execution plans._

## Backlog

### Async HTTP Migration
- Replace `requests` with `httpx` for true async API calls
- Unblock the asyncio event loop during EDB API interactions
- See [tech-debt-tracker.md](exec-plans/tech-debt-tracker.md) TD-001

### Connection Pooling
- HTTP session reuse for EDB API calls
- Reduce TCP handshake overhead on repeated calls
- See [tech-debt-tracker.md](exec-plans/tech-debt-tracker.md) TD-002

### Test Infrastructure
- Add pytest with mocked API responses
- Unit tests for validation, schema tests for Pydantic models, tool tests with mocked HTTP
- See [tech-debt-tracker.md](exec-plans/tech-debt-tracker.md) TD-003

### Tool Schema Validation at Registration
- Auto-validate tool inputs against Pydantic schemas at registration time
- Catch schema mismatches before runtime

## Completed

_No completed plans yet._

## Navigation

- Active plans: [exec-plans/active/](exec-plans/active/)
- Completed plans: [exec-plans/completed/](exec-plans/completed/)
- Tech debt: [exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md)
