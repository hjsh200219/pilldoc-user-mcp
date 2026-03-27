# Product Sense

## What This Product Does

PillDoc User MCP is an internal operations tool that gives AI agents (Claude Desktop, IDE agents) direct access to PillDoc pharmacy management data. It enables customer support, data analysis, and pharmacy account management tasks through natural language interaction.

## Users

- **Internal Operations Team**: Uses Claude Desktop to manage pharmacy accounts, check campaign status, look up pharmacy info
- **Data Analysts**: Queries national medical institution data and PillDoc subscriber statistics
- **Developers**: Uses IDE agents for debugging and API exploration

## Core Value Proposition

1. **Natural language operations**: Instead of navigating admin dashboards, operators ask Claude to find/update pharmacy data
2. **Data source disambiguation**: The system prompt guides AI agents to pick the correct data source (national DB vs PillDoc subscribers)
3. **Error-tolerant input**: Field auto-mapping and Content-Type retry handle common mistakes transparently

## Tool Domains & Use Cases

| Domain | Primary Use Case |
|--------|-----------------|
| Auth | Login and token management for API access |
| Accounts | Pharmacy account CRUD, batch statistics |
| Pharmacy | Individual pharmacy/user detail lookup |
| Campaign | Ad campaign block/unblock management |
| Statistics | ERP and regional distribution reports |
| Medical Institution | Institution code parsing and validation |
| Product Orders | Order tracking, summaries, date-range reports |
| National Institutions | Nationwide medical facility data queries |

## Key Metrics (if tracked)

- Tool call count, success rate, avg latency per tool (via `utils/metrics.py`)
- No external monitoring dashboard; metrics are in-memory only
