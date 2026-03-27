# PillDoc User MCP - Architecture

## Overview

Local MCP (Model Context Protocol) server providing pharmacy account management, user lookup, campaign management, medical institution data, and product order tools for MCP-compatible clients.

**Runtime**: Python 3.9+ | **Protocol**: MCP over stdio | **Framework**: FastMCP (primary), Standard MCP SDK (alternate)

## Directory Structure

```
src/
  __init__.py
  __main__.py
  mcp_server.py              # FastMCP entry - on-demand module loading
  server.py                  # Standard MCP SDK entry (alternate)
  mcp_server_improved.py     # Experimental improved server
  main_server.py             # Alternative main server
  config.py                  # Pydantic Settings (singleton via get_settings())
  login_jwt.py               # CLI login utility
  tool_registry.py           # Tool registration utilities
  register_tools.py          # Tool registration helper

  auth/                      # Authentication module
    __init__.py
    login.py                 # login_and_get_token() - HTTP POST to sign-in endpoint
    manager.py               # AuthManager class - token lifecycle

  handlers/                  # MCP protocol handlers
    __init__.py
    tools.py                 # Tool list/call handler (Standard SDK path)
    resources.py             # Resource provider handler
    prompts.py               # Prompt provider handler

  mcp_tools/                 # Tool definitions per domain (THE integration layer)
    __init__.py              # Exports register_*_tools functions
    auth_tools.py            # login tool
    accounts_tools.py        # get_accounts, update_account, get_accounts_stats, etc.
    pilldoc_pharmacy_tools.py    # get_user, get_pharm, find_pharm
    pilldoc_service_tools.py     # Composite: accounts + pharmacy + campaign + statistics
    campaign_tools.py            # get_adps_rejects, update_adps_reject
    pilldoc_statistics_tools.py  # get_erp_statistics, get_region_statistics
    medical_institution_tools.py     # parse/validate/analyze institution codes
    product_orders_tools.py          # get_product_orders, get_order_summary
    national_medical_institutions_tools.py  # PostgreSQL institutions queries
    filter_builder.py        # Query filter construction helpers
    helpers.py               # Shared tool helpers (auth resolution, etc.)

  schemas/                   # Pydantic models (pure data, no logic)
    __init__.py
    auth.py                  # LoginRequest, LoginResponse
    accounts.py              # AccountFilter, AccountInfo, AccountStats
    common.py                # PaginationParams, ErrorResponse, BaseResponse
    pharmacy.py              # Pharmacy-related models
    statistics.py            # Statistics-related models

  pilldoc/                   # EDB Admin API client
    __init__.py
    api.py                   # APIClient, get_accounts(), get_user(), update_account(), etc.

  utils/                     # Utilities (zero internal deps)
    __init__.py
    config.py                # Config utilities
    errors.py                # MCPError hierarchy, @handle_error decorator
    logging.py               # setup_logging(), @log_tool_call, LogContext
    metrics.py               # Metrics singleton, @track_execution
    validation.py            # validate_arguments(), validate_email/phone/biz_number
```

## Data Flow

```
Claude Desktop / MCP Client
  |  (stdio, JSON-RPC)
  v
FastMCP Server (mcp_server.py)
  |  On-Demand Module Loader (_TOOL_TO_MODULE, _MODULE_LOADERS)
  v
Tool Registry (mcp_tools/)
  |  Auth resolution + Input validation + Field auto-mapping
  v
API Client (pilldoc/api.py)         Database (psycopg2)
  |  HTTP requests                    |  PostgreSQL queries
  v                                   v
EDB Admin API (HTTPS)              salesdb.institutions
```

## On-Demand Loading

Tools are mapped to 5 module groups in `mcp_server.py`:

| Module Group | Tools | Loader |
|-------------|-------|--------|
| `auth` | login | `register_auth_tools` |
| `pilldoc_service` | get_accounts, update_account, get_user, get_pharm, find_pharm, get_adps_rejects, get_erp_statistics, get_region_statistics | `register_pilldoc_service_tools` |
| `medical_institution` | parse/validate/analyze_medical_institution_code | `register_medical_institution_tools` |
| `product_orders` | get_product_orders, get_order_summary, get_orders_by_date_range, get_orders_by_pharmacy | `register_product_orders_tools` |
| `national_medical_institutions` | get_institutions, distribution, schema, stats, execute_query | `register_national_medical_institutions_tools` |

## Layer Rules

Imports flow **downward only**:

```
Entry (mcp_server.py, server.py)
  v
Handlers (handlers/)
  v
Tool Registration (mcp_tools/)
  v
Schemas (schemas/)  |  Business Logic (pilldoc/)  |  Auth (auth/)
  v                    v                              v
Utils (utils/, tools/base.py) - zero internal deps
```

Full rules: [docs/design-docs/layer-rules.md](docs/design-docs/layer-rules.md)

## External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >=1.14.0 | MCP SDK + FastMCP |
| `requests` | >=2.31.0 | HTTP client for EDB API |
| `pydantic` | >=2.0.0 | Schema validation |
| `pydantic-settings` | >=2.0.0 | Env-based config |
| `python-dotenv` | >=1.0.1 | .env file loading |
| `psycopg2-binary` | >=2.9.0 | PostgreSQL (institutions DB) |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EDB_BASE_URL` | Yes | `https://dev-adminapi.edbintra.co.kr` | EDB Admin API base |
| `EDB_LOGIN_URL` | No | `{base}/v1/member/sign-in` | Login endpoint override |
| `EDB_USER_ID` | No | - | Default login user |
| `EDB_PASSWORD` | No | - | Default login password |
| `EDB_FORCE_LOGIN` | No | `false` | Force re-login |
| `MCP_ON_DEMAND` | No | `true` | Lazy module loading |
| `DATABASE_URL` | No | - | PostgreSQL connection |

## Related Documentation

- [AGENTS.md](AGENTS.md) - Agent navigation map
- [docs/DESIGN.md](docs/DESIGN.md) - Design overview and key decisions
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed architecture
- [docs/RELIABILITY.md](docs/RELIABILITY.md) - Error handling and resilience
- [docs/SECURITY.md](docs/SECURITY.md) - Security considerations
