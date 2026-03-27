# Database Schema

## PostgreSQL: salesdb

### institutions (National Medical Institutions)

This table is accessed read-only via `national_medical_institutions_tools`. Schema is introspected at runtime via `get_institutions_schema`.

**Access Pattern**: SELECT-only queries with parameterized inputs. Write operations are rejected at the tool level.

**Connection**: Configured via `DATABASE_URL` environment variable (`postgresql://user:password@host:port/database`).

**Tools that access this table**:
- `get_institutions` - Query with filters (name, type, region)
- `get_institutions_distribution_by_region_and_type` - Aggregated distribution
- `get_institutions_schema` - Runtime schema introspection
- `get_institutions_stats` - Summary statistics
- `execute_institutions_query` - Custom SELECT queries

**Default Limits**:
- `limit=100` per query (configurable)
- Parameterized queries to prevent SQL injection

## EDB Admin API (External - Not Direct DB)

The following data is accessed through the EDB Admin API HTTP endpoints, not direct database access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/member/sign-in` | POST | Authentication |
| `/v1/pilldoc/accounts` | POST | List/search accounts |
| `/v1/pilldoc/account/{id}` | PATCH | Update account |
| `/v1/pilldoc/user/{id}` | GET | User detail |
| `/v1/pilldoc/pharm/{bizno}` | GET | Pharmacy detail |
| `/v1/adps/campain/{bizno}/reject` | GET/POST | Campaign reject management |

_Note: Full database schema for EDB is not available locally. The MCP server acts as a client to the EDB Admin API._
