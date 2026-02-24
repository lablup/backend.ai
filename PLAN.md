# Implementation Plan: BA-4564

> Add model_serving domain test scenarios via Client SDK v2

## SDK v2 Client Analysis

**File:** `src/ai/backend/client/v2/domains/model_serving.py`
**Class:** `ModelServingClient` (extends `BaseDomainClient`)
**API Prefix:** `/services`

| # | Method | HTTP | Endpoint | Params Style | Notes |
|---|--------|------|----------|-------------|-------|
| 1 | `list_serve(name?)` | GET | `/services` | query params (optional `name`) | No body; `params={"name": ...}` when name provided |
| 2 | `search_services(request)` | POST | `/services/_/search` | JSON body (`SearchServicesRequestModel`) | Filter + pagination |
| 3 | `get_info(service_id)` | GET | `/services/{service_id}` | path param only | No body, no query params |
| 4 | `create(request)` | POST | `/services` | JSON body (`NewServiceRequestModel`) | Complex validation: VFolder, scaling group, image |
| 5 | `try_start(request)` | POST | `/services/_/try` | JSON body (`NewServiceRequestModel`) | Same validation as create; returns task_id |
| 6 | `delete(service_id)` | DELETE | `/services/{service_id}` | path param only | Destroys deployment |
| 7 | `sync(service_id)` | POST | `/services/{service_id}/sync` | path param only | Force-syncs with AppProxy |
| 8 | `scale(service_id, request)` | POST | `/services/{service_id}/scale` | path + JSON body (`ScaleRequestModel`) | `to: int` target replicas |
| 9 | `update_route(service_id, route_id, request)` | PUT | `/services/{sid}/routings/{rid}` | path + JSON body (`UpdateRouteRequestModel`) | `traffic_ratio: float` |
| 10 | `delete_route(service_id, route_id)` | DELETE | `/services/{sid}/routings/{rid}` | path params only | Removes specific route |
| 11 | `generate_token(service_id, request)` | POST | `/services/{service_id}/token` | path + JSON body (`TokenRequestModel`) | Needs AppProxy for token generation |
| 12 | `list_errors(service_id)` | GET | `/services/{service_id}/errors` | path param only | Returns error list + retry count |
| 13 | `clear_error(service_id)` | POST | `/services/{service_id}/errors/clear` | path param only | Returns 204 No Content |
| 14 | `list_supported_runtimes()` | GET | `/services/_/runtimes` | none | Static data from RuntimeVariant enum |

### Request Model Key Fields

- **NewServiceRequestModel**: `service_name` (4-80 chars, pattern `^\w[\w-]*\w$`), `replicas` (int), `config` (ServiceConfigModel with `model` + `scaling_group` required)
- **SearchServicesRequestModel**: `filter` (optional), `offset` (default 0), `limit` (default 20, max 100)
- **ScaleRequestModel**: `to` (int, target session count)
- **UpdateRouteRequestModel**: `traffic_ratio` (float >= 0)
- **TokenRequestModel**: `duration` or `valid_until` (one required), validator checks expiry not in past

## Server Handler Status

- **Handler file:** `src/ai/backend/manager/api/service.py` — **EXISTS** (single module, not a package)
- **Registered in `global_subapp_pkgs`:** **YES** as `.service`
- **Action required:** Test-only (no handler implementation needed)

### Handler Architecture

All handlers follow the pattern: `Handler → Action → Processor → Service → Repository`

Key processors:
- `processors.model_serving.list_model_service` — list_serve
- `processors.model_serving.search_services` — search_services
- `processors.model_serving.get_model_service_info` — get_info
- `processors.deployment.create_legacy_deployment` — create
- `processors.deployment.destroy_deployment` — delete
- `processors.model_serving.dry_run_model_service` — try_start
- `processors.model_serving.force_sync` — sync
- `processors.model_serving_auto_scaling.scale_service_replicas` — scale
- `processors.model_serving.update_route` — update_route
- `processors.model_serving.delete_route` — delete_route
- `processors.model_serving.generate_token` — generate_token
- `processors.model_serving.list_errors` — list_errors
- `processors.model_serving.clear_error` — clear_error

### HMAC Signing Analysis

In `base_client.py._request()`:
```python
rel_url = "/" + path.lstrip("/")
headers = self._sign(method, rel_url, content_type)  # signs "/services"
# ...
async with session.request(method, url, ..., params=params):  # URL becomes "/services?name=xxx"
```
Client signs HMAC over path only (`/services`), but server verifies against `request.raw_path` (`/services?name=xxx`).

**Affected method:** `list_serve(name=...)` — GET with query params → HMAC mismatch → 401.
**Unaffected:** `list_serve()` (no name) — no query params, paths match.

> **Scope note**: Only `list_serve(name=...)` (1 test) is HMAC-affected and uses xfail. All other 15 component test scenarios (Tier 1 and Tier 2) proceed normally without xfail. Integration tests must not call `list_serve(name=...)` — lifecycle tests use `list_serve()` (no filter) or skip list-with-filter entirely.

## Test Scenarios

### Component Tests (`tests/component/model_serving/`)

#### Tier 1: Stateless Read Endpoints (no service setup required)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestListServe` | `test_admin_lists_empty_services` | GET /services with no services → empty list | - |
| `TestListServe` | `test_user_lists_empty_services` | Regular user GET /services → empty list | - |
| `TestListServe` | `test_list_serve_with_name_filter` | GET /services?name=... → 401 | HMAC bug |
| `TestSearchServices` | `test_admin_searches_empty_services` | POST /services/_/search → empty results with pagination | - |
| `TestSearchServices` | `test_search_with_pagination` | POST with offset/limit → valid pagination response | - |
| `TestListSupportedRuntimes` | `test_admin_lists_runtimes` | GET /services/_/runtimes → non-empty runtime list | - |
| `TestListSupportedRuntimes` | `test_user_lists_runtimes` | Regular user → same runtime list | - |

#### Tier 2: Error Handling for Non-existent Services

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestGetInfo` | `test_get_info_nonexistent_service` | GET /services/{random_uuid} → error | - |
| `TestDeleteService` | `test_delete_nonexistent_service` | DELETE /services/{random_uuid} → error | - |
| `TestSync` | `test_sync_nonexistent_service` | POST /services/{random_uuid}/sync → error | - |
| `TestScale` | `test_scale_nonexistent_service` | POST /services/{random_uuid}/scale → error | - |
| `TestUpdateRoute` | `test_update_route_nonexistent_service` | PUT /services/{sid}/routings/{rid} → error | - |
| `TestDeleteRoute` | `test_delete_route_nonexistent_service` | DELETE /services/{sid}/routings/{rid} → error | - |
| `TestGenerateToken` | `test_generate_token_nonexistent_service` | POST /services/{random_uuid}/token → error | - |
| `TestListErrors` | `test_list_errors_nonexistent_service` | GET /services/{random_uuid}/errors → error | - |
| `TestClearError` | `test_clear_error_nonexistent_service` | POST /services/{random_uuid}/errors/clear → error | - |

### Integration Tests (`tests/integration/model_serving/`)

| Test Class | Scenario |
|------------|----------|
| `TestModelServingLifecycle` | create → get_info → list_serve → search → scale → delete |
| `TestModelServingTokens` | create → generate_token → delete |
| `TestModelServingErrors` | create → list_errors → clear_error → delete |
| `TestModelServingRoutes` | create → update_route → delete_route → delete |

**Note:** Integration tests require full infrastructure (agents, AppProxy, storage proxy, images) and are structured as lifecycle scenarios.

## Deferred Items

| Item | Reason |
|------|--------|
| `create()` / `try_start()` in component tests | Requires model VFolder + scaling group + image + storage proxy model definition validation. Too complex for component test fixtures. Covered in integration tests. |
| `sync()` happy path | Requires AppProxy connection (mocked in component tests). Cannot verify actual sync behavior. |
| `generate_token()` happy path | Requires AppProxy for token generation. Token creation delegated to external service. |
| WebSocket/SSE streaming | Not part of this SDK client. No streaming endpoints in ModelServingClient. |

## conftest.py Design

### Required Fixtures

1. **`server_subapp_pkgs()`** → `[".auth", ".service"]`
2. **`server_cleanup_contexts()`** → standard cleanup chain + `_model_serving_domain_ctx`
3. **`_model_serving_domain_ctx(root_ctx)`** → Repositories + Processors init (same pattern as ACL/vfolder)

### Additional Mock Requirements

The `_model_serving_domain_ctx` must mock:
- `config_provider._legacy_etcd_config_loader.get_manager_status` → `ManagerStatus.RUNNING`
- `config_provider._legacy_etcd_config_loader.get_vfolder_types` → `["user", "group"]` (needed for create validation)

Static import for Pants: `from ai.backend.manager.api import service as _service_api`

## Implementation Steps

1. Create `tests/component/model_serving/__init__.py`
2. Create `tests/component/model_serving/conftest.py` (domain context, fixtures)
3. Create `tests/component/model_serving/test_model_serving.py` (Tier 1 + Tier 2 tests)
4. Create `tests/component/model_serving/BUILD` (`python_tests()`)
5. Create `tests/integration/model_serving/__init__.py`
6. Create `tests/integration/model_serving/conftest.py` (domain context, fixtures)
7. Create `tests/integration/model_serving/test_model_serving.py` (lifecycle tests)
8. Create `tests/integration/model_serving/BUILD` (`python_tests()`)
9. Run `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
