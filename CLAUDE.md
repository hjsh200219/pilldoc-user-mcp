# pilldoc-user-mcp

Local MCP server for PillDoc pharmacy management (accounts, users, campaigns, statistics, orders, medical institutions).

## Quick Reference

- **Language**: Python 3.9+ | **Framework**: FastMCP (mcp>=1.14.0)
- **Protocol**: MCP over stdio | **Entry**: `python -m src.mcp_server`
- **Config**: `.env.local` (pydantic-settings based)

## Project Map

```
src/
  mcp_server.py          # FastMCP entry - on-demand module loading
  server.py              # Standard MCP SDK entry (alternate)
  config.py              # Pydantic Settings (singleton)
  auth/                  # Login flow, AuthManager
  handlers/              # MCP protocol handlers (tools, resources, prompts)
  mcp_tools/             # Tool definitions per domain (THE integration layer)
  schemas/               # Pydantic request/response models
  pilldoc/               # EDB Admin API client
  utils/                 # Config, errors, logging, metrics, validation
  tools/                 # BaseTool abstract class, ToolRegistry
```

## Architecture Docs

| Document | Path |
|----------|------|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Quality | [docs/QUALITY.md](docs/QUALITY.md) |
| Reliability | [docs/RELIABILITY.md](docs/RELIABILITY.md) |
| Layer Rules | [docs/design-docs/layer-rules.md](docs/design-docs/layer-rules.md) |
| Product Specs | [docs/product-specs/index.md](docs/product-specs/index.md) |

## Key Patterns

1. **On-demand loading**: Modules load on first tool call (env `MCP_ON_DEMAND=true`)
2. **Dual entry**: `mcp_server.py` (FastMCP) vs `server.py` (Standard SDK)
3. **Auth fallback**: Auto-login from env vars; tools also accept explicit token/credentials
4. **Field auto-mapping**: Update tools convert common Korean/English field names automatically
5. **Content-Type retry**: PATCH requests retry with different Content-Types on 415

## Tool Domains

| Domain | Module | Key Tools |
|--------|--------|-----------|
| Auth | `auth_tools` | `login` |
| Accounts | `accounts_tools` | `get_accounts`, `update_account`, `get_accounts_stats` |
| Pharmacy | `pilldoc_pharmacy_tools` | `get_user`, `get_pharm`, `find_pharm` |
| Campaign | `campaign_tools` | `get_adps_rejects`, `update_adps_reject` |
| Statistics | `pilldoc_statistics_tools` | `get_erp_statistics`, `get_region_statistics` |
| Med. Institution | `medical_institution_tools` | `parse/validate/analyze_medical_institution_code` |
| Orders | `product_orders_tools` | `get_product_orders`, `get_order_summary` |
| National DB | `national_medical_institutions_tools` | `get_institutions`, `execute_institutions_query` |

## Layer Rules (summary)

Imports flow **downward only**: Entry -> Handlers -> mcp_tools -> schemas/pilldoc/auth -> utils

- `utils/` and `tools/base.py` have zero internal dependencies
- `schemas/` are pure Pydantic models (no logic)
- `pilldoc/api.py` is auth-agnostic (receives token as param)
- `mcp_tools/` is the integration layer (glues auth + API + validation + MCP)

See [docs/design-docs/layer-rules.md](docs/design-docs/layer-rules.md) for full rules.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run
python -m src.mcp_server

# Env
cp .env.example .env.local  # Set EDB_BASE_URL, EDB_USER_ID, EDB_PASSWORD
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `EDB_BASE_URL` | Yes | `https://dev-adminapi.edbintra.co.kr` |
| `EDB_LOGIN_URL` | No | `{base}/v1/member/sign-in` |
| `EDB_USER_ID` | No | - |
| `EDB_PASSWORD` | No | - |
| `MCP_ON_DEMAND` | No | `true` |
| `DATABASE_URL` | No | - (PostgreSQL for institutions) |
