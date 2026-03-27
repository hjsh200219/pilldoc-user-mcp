# AGENTS.md - pilldoc-user-mcp

> Agent-first navigation map. Start here, then follow links.

## Quick Start

- **What**: Local MCP server for PillDoc pharmacy management
- **Stack**: Python 3.9+ | FastMCP | MCP over stdio
- **Entry**: `python -m src.mcp_server`
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

## Architecture Rules

1. **Imports flow downward only**: Entry > Handlers > mcp_tools > schemas/pilldoc/auth > utils
2. **utils/ has zero internal deps**: Only stdlib + third-party
3. **schemas/ are pure data**: No logic, no API calls, no side effects
4. **pilldoc/api.py is auth-agnostic**: Receives token as parameter
5. **mcp_tools/ owns the glue**: Auth + API + validation + MCP registration

## Tool Domains (8 domains, 25+ tools)

| Domain | Module | Example Tools |
|--------|--------|---------------|
| Auth | `auth_tools` | `login` |
| Accounts | `accounts_tools` | `get_accounts`, `update_account` |
| Pharmacy | `pilldoc_pharmacy_tools` | `get_user`, `find_pharm` |
| Campaign | `campaign_tools` | `get_adps_rejects` |
| Statistics | `pilldoc_statistics_tools` | `get_erp_statistics` |
| Med. Institution | `medical_institution_tools` | `parse_medical_institution_code` |
| Orders | `product_orders_tools` | `get_product_orders` |
| National DB | `national_medical_institutions_tools` | `get_institutions` |

## Key Patterns

- **On-demand loading**: Modules load on first tool call (`MCP_ON_DEMAND=true`)
- **Auth fallback**: Auto-login from env; tools also accept explicit credentials
- **Field auto-mapping**: Korean/English field names auto-converted
- **Content-Type retry**: PATCH retries with different Content-Types on 415

## Documentation Map

| Document | Path | Purpose |
|----------|------|---------|
| Design Overview | [docs/DESIGN.md](docs/DESIGN.md) | Architecture pattern, key decisions |
| Core Beliefs | [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md) | Guiding principles |
| Layer Rules | [docs/design-docs/layer-rules.md](docs/design-docs/layer-rules.md) | Import constraints |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, layers, data flow |
| Product Specs | [docs/product-specs/index.md](docs/product-specs/index.md) | Tool domain specifications |
| Product Sense | [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md) | Users, value prop, use cases |
| Quality | [docs/QUALITY.md](docs/QUALITY.md) | Code quality standards |
| Quality Score | [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md) | Current assessment (6/10) |
| Reliability | [docs/RELIABILITY.md](docs/RELIABILITY.md) | Error handling, resilience |
| Security | [docs/SECURITY.md](docs/SECURITY.md) | Auth, data access, sensitive data |
| DB Schema | [docs/generated/db-schema.md](docs/generated/db-schema.md) | Database and API schema |
| Plans | [docs/PLANS.md](docs/PLANS.md) | Active/backlog execution plans |
| Tech Debt | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) | Tracked technical debt |
| Frontend | [docs/FRONTEND.md](docs/FRONTEND.md) | N/A (backend MCP server) |

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run
python -m src.mcp_server

# Env
cp .env.example .env.local  # Set EDB_BASE_URL, EDB_USER_ID, EDB_PASSWORD
```
