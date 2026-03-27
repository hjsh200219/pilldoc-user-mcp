# Product Specifications

## MCP Tool Domains

### 1. Authentication (`auth_tools`)
- Login with userId/password
- Token management (auto-login, manual login, force re-login)

### 2. Pharmacy Account Management (`accounts_tools`)
- List/search PillDoc accounts with filters (ERP, ad display, sales channel, chain)
- Update account fields (PATCH with auto-field-mapping)
- Search-then-update workflow (find by name/bizNo, then update)
- Account statistics aggregation (monthly, region, ERP, ad status)

### 3. Pharmacy Info (`pilldoc_pharmacy_tools`)
- Get user detail by ID
- Get pharmacy detail by business number
- Find pharmacy by name or business number
- Combined search returning account + user + pharm + adpsRejects

### 4. Campaign Management (`campaign_tools`)
- List rejected/blocked campaigns for a pharmacy
- Block/unblock campaign with comment

### 5. PillDoc Statistics (`pilldoc_statistics_tools`)
- ERP code distribution and print counts
- Region-based pharmacy distribution and print counts

### 6. Medical Institution Code (`medical_institution_tools`)
- Parse 8-digit institution code (region, type, serial)
- Validate institution code format
- Batch analysis of multiple codes

### 7. Product Orders (`product_orders_tools`)
- List orders with filters (date, status, pharmacy, search)
- Order summary and aggregation
- Date-range order reports
- Per-pharmacy order history

### 8. National Medical Institutions (`national_medical_institutions_tools`)
- Query PostgreSQL institutions table (nationwide medical facilities)
- Distribution by region and facility type
- Schema introspection
- Statistics overview
- Custom SQL queries (SELECT only)
