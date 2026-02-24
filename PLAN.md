# Implementation Plan: BA-4589

## SDK v2 Client Analysis

**File:** `src/ai/backend/client/v2/domains/system.py`

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `registry.system.get_versions()` | GET | `/` | none | Returns `SystemVersionResponse(version, manager)` |

**DTO:** `src/ai/backend/common/dto/manager/system/response.py` → `SystemVersionResponse` with fields `version: str` and `manager: str`.

**Registry access:** `BackendAIClientRegistry.system` → `SystemClient(BaseDomainClient)`

Only **1 method** exists in the SDK v2 SystemClient.

## Server Handler Status

- **Handler package:** NOT a subapp — `hello()` is registered directly on the root app in `build_root_app()` (`server.py:1638-1639`)
- **Registered in `global_subapp_pkgs`:** N/A — not a subapp; it's a root-level route
- **Action required:** **test-only** (handler already exists at `server.py:377-384`)

### Key architecture details

1. `hello()` at `GET /` and `GET ""` is registered on the **root app**, not via a subapp package.
2. `hello()` does **NOT** use `@auth_required` — it is an unauthenticated endpoint.
3. When `.auth` subapp is loaded, `auth_middleware` becomes a global middleware on the root app. However, it checks `get_handler_attr(request, "auth_required", False)` and **skips auth** for handlers without the decorator (line 744).
4. HMAC headers sent by the client SDK are harmless — the middleware processes them but doesn't enforce auth.
5. Response: `{"version": LATEST_API_VERSION, "manager": __version__}` (hardcoded values, no DB access).

## Test Scenarios

### Component Tests (`tests/component/system/`)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestGetVersions` | `test_admin_gets_versions` | Admin calls `get_versions()` → returns `SystemVersionResponse` | - |
| `TestGetVersions` | `test_user_gets_versions` | Regular user calls `get_versions()` → returns `SystemVersionResponse` | - |
| `TestGetVersions` | `test_response_contains_valid_version_strings` | Verify `version` starts with `"v"` and `manager` is non-empty | - |

**conftest.py notes:**
- `server_subapp_pkgs()` → `[]` (no subapps needed; `hello` is on root app)
- `server_cleanup_contexts()` → `[]` (no production contexts needed; handler has no DB/Redis/etc dependencies)
- No `_system_domain_ctx` needed (no repositories or processors)
- Static import: none required (no subapp modules to pull into PEX)

### Integration Tests (`tests/integration/system/`)

| Test Class | Test Method | Scenario |
|------------|-------------|----------|
| `TestGetVersions` | `test_admin_gets_versions` | Full-stack server admin call to `get_versions()` |
| `TestGetVersions` | `test_user_gets_versions` | Full-stack server user call to `get_versions()` |
| `TestGetVersions` | `test_response_version_format` | Verify version string format with full server |

**conftest.py notes:**
- Integration conftest uses `server_factory` (full-stack, all subapps, all cleanup contexts)
- No domain-specific overrides needed — just an empty conftest with `@pytest.mark.integration` support

## Deferred Items

| Item | Reason |
|------|--------|
| (none) | `SystemClient` has only one simple GET endpoint with no streaming/WebSocket |

## Known SDK Bugs Assessment

| Bug | Applies? | Reason |
|-----|----------|--------|
| HMAC query param bug | **NO** | `GET /` has no query params |
| GET JSON body bug | **NO** | `get_versions()` sends no JSON body |
| Streaming (WS/SSE) | **NO** | No streaming methods |

## Existing Tests

- **Unit tests:** `tests/unit/client_v2/test_system_client.py` (mock-based, verifies SDK client logic)
- **Component tests:** none
- **Integration tests:** none

## Implementation Steps

1. Create `tests/component/system/__init__.py`
2. Create `tests/component/system/conftest.py` (override `server_subapp_pkgs` and `server_cleanup_contexts`)
3. Create `tests/component/system/test_system.py` (3 test methods)
4. Create `tests/component/system/BUILD` (`python_tests()`)
5. Create `tests/integration/system/__init__.py`
6. Create `tests/integration/system/conftest.py` (minimal, no overrides needed)
7. Create `tests/integration/system/test_system.py` (3 test methods with `@pytest.mark.integration`)
8. Create `tests/integration/system/BUILD` (`python_tests()`)
9. Run `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
