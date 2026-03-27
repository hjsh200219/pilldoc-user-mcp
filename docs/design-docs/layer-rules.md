# Layer Dependency Rules

## Layer Hierarchy (top = outermost)

```
┌─────────────────────────────────────────────┐
│  Entry Points                               │
│  src/mcp_server.py, src/server.py           │
├─────────────────────────────────────────────┤
│  Handlers                                   │
│  src/handlers/ (tools, resources, prompts)   │
├─────────────────────────────────────────────┤
│  Tool Registration                          │
│  src/mcp_tools/*_tools.py                   │
├─────────────────────────────────────────────┤
│  Schemas                                    │
│  src/schemas/ (Pydantic models)             │
├─────────────────────────────────────────────┤
│  Business Logic                             │
│  src/pilldoc/ (API clients)                 │
├─────────────────────────────────────────────┤
│  Auth                                       │
│  src/auth/ (login, token manager)           │
├─────────────────────────────────────────────┤
│  Utilities                                  │
│  src/utils/ (config, errors, logging,       │
│              metrics, validation)            │
│  src/tools/base.py (BaseTool, decorators)   │
└─────────────────────────────────────────────┘
```

## Rules

### R1: Imports flow downward only
A layer may only import from layers below it. Never import upward.

```
OK:   mcp_tools/accounts_tools.py  ->  pilldoc/api.py
OK:   mcp_tools/accounts_tools.py  ->  utils/validation.py
OK:   handlers/tools.py            ->  mcp_tools/__init__.py
FAIL: utils/validation.py          ->  mcp_tools/accounts_tools.py
FAIL: pilldoc/api.py               ->  handlers/tools.py
```

### R2: Utils has zero internal dependencies
`src/utils/` and `src/tools/base.py` must not import from any other `src/` module (except standard library and third-party packages).

### R3: Schemas are pure data
`src/schemas/` contains only Pydantic models. No business logic, no API calls, no side effects.

### R4: Business logic is auth-agnostic
`src/pilldoc/api.py` receives `token` as a parameter. It must not import from `src/auth/` or manage authentication state.

### R5: Tool registration owns the glue
`src/mcp_tools/*_tools.py` is the only place where auth helpers, API clients, validation, and MCP tool definitions come together. This is the integration layer.

### R6: Entry points do not contain business logic
`mcp_server.py` and `server.py` handle only server creation, module loading strategy, and lifecycle. No tool implementation code.

### R7: On-demand loading preserves boundaries
The on-demand loader in `mcp_server.py` uses `__import__` to lazily load modules. Each module must be self-contained enough to load independently without side effects on other modules.

## Allowed Cross-Layer Imports

| From | May Import |
|------|-----------|
| Entry (`mcp_server.py`, `server.py`) | handlers, auth, utils, mcp_tools (via loader) |
| Handlers (`handlers/`) | mcp_tools |
| Tool Registration (`mcp_tools/`) | pilldoc, auth, utils, schemas, tools/base |
| Schemas (`schemas/`) | (none from src) |
| Business Logic (`pilldoc/`) | utils |
| Auth (`auth/`) | utils |
| Utils (`utils/`, `tools/base.py`) | (none from src) |
