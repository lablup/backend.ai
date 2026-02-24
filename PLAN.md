# Implementation Plan: BA-4566

## SDK v2 Client Analysis

FairShareClient has **27 methods** across 6 categories.

### Domain Fair Share (4 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 1 | `get_domain_fair_share(rg, domain)` | GET | `/fair-share/domains/{rg}/{domain}` | path | superadmin |
| 2 | `search_domain_fair_shares(req)` | POST | `/fair-share/domains/search` | body | superadmin |
| 3 | `rg_get_domain_fair_share(rg, domain)` | GET | `/fair-share/rg/{rg}/domains/{domain}` | path | auth only |
| 4 | `rg_search_domain_fair_shares(rg, req)` | POST | `/fair-share/rg/{rg}/domains/search` | body | auth only |

### Project Fair Share (4 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 5 | `get_project_fair_share(rg, project_id)` | GET | `/fair-share/projects/{rg}/{project_id}` | path | superadmin |
| 6 | `search_project_fair_shares(req)` | POST | `/fair-share/projects/search` | body | superadmin |
| 7 | `rg_get_project_fair_share(rg, domain, project_id)` | GET | `/fair-share/rg/{rg}/domains/{domain}/projects/{project_id}` | path | auth only |
| 8 | `rg_search_project_fair_shares(rg, domain, req)` | POST | `/fair-share/rg/{rg}/domains/{domain}/projects/search` | body | auth only |

### User Fair Share (4 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 9 | `get_user_fair_share(rg, project_id, user_uuid)` | GET | `/fair-share/users/{rg}/{project_id}/{user_uuid}` | path | superadmin |
| 10 | `search_user_fair_shares(req)` | POST | `/fair-share/users/search` | body | superadmin |
| 11 | `rg_get_user_fair_share(rg, domain, project_id, user_uuid)` | GET | `/fair-share/rg/{rg}/domains/{domain}/projects/{project_id}/users/{user_uuid}` | path | auth only |
| 12 | `rg_search_user_fair_shares(rg, domain, project_id, req)` | POST | `/fair-share/rg/{rg}/domains/{domain}/projects/{project_id}/users/search` | body | auth only |

### Usage Buckets (6 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 13 | `search_domain_usage_buckets(req)` | POST | `/fair-share/usage-buckets/domains/search` | body | superadmin |
| 14 | `search_project_usage_buckets(req)` | POST | `/fair-share/usage-buckets/projects/search` | body | superadmin |
| 15 | `search_user_usage_buckets(req)` | POST | `/fair-share/usage-buckets/users/search` | body | superadmin |
| 16 | `rg_search_domain_usage_buckets(rg, req)` | POST | `/fair-share/rg/{rg}/usage-buckets/domains/search` | body | auth only |
| 17 | `rg_search_project_usage_buckets(rg, domain, req)` | POST | `/fair-share/rg/{rg}/domains/{domain}/usage-buckets/projects/search` | body | auth only |
| 18 | `rg_search_user_usage_buckets(rg, domain, project_id, req)` | POST | `/fair-share/rg/{rg}/domains/{domain}/projects/{project_id}/usage-buckets/users/search` | body | auth only |

### Upsert Weights (3 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 19 | `upsert_domain_fair_share_weight(rg, domain, req)` | PUT | `/fair-share/domains/{rg}/{domain}/weight` | path+body | superadmin |
| 20 | `upsert_project_fair_share_weight(rg, project_id, req)` | PUT | `/fair-share/projects/{rg}/{project_id}/weight` | path+body | superadmin |
| 21 | `upsert_user_fair_share_weight(rg, project_id, user_uuid, req)` | PUT | `/fair-share/users/{rg}/{project_id}/{user_uuid}/weight` | path+body | superadmin |

### Bulk Upsert Weights (3 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 22 | `bulk_upsert_domain_fair_share_weight(req)` | POST | `/fair-share/domains/bulk-upsert-weight` | body | superadmin |
| 23 | `bulk_upsert_project_fair_share_weight(req)` | POST | `/fair-share/projects/bulk-upsert-weight` | body | superadmin |
| 24 | `bulk_upsert_user_fair_share_weight(req)` | POST | `/fair-share/users/bulk-upsert-weight` | body | superadmin |

### Resource Group Fair Share Spec (3 methods)
| # | Method | HTTP | Endpoint | Params | Auth |
|---|--------|------|----------|--------|------|
| 25 | `get_resource_group_fair_share_spec(rg)` | GET | `/fair-share/resource-groups/{rg}/spec` | path | superadmin |
| 26 | `search_resource_group_fair_share_specs()` | GET | `/fair-share/resource-groups/specs` | none | superadmin |
| 27 | `update_resource_group_fair_share_spec(rg, req)` | PATCH | `/fair-share/resource-groups/{rg}/spec` | path+body | superadmin |

## Server Handler Status

- **Handler package**: EXISTS at `src/ai/backend/manager/api/fair_share/handler.py`
- **Registered in `global_subapp_pkgs`**: YES (line 364 of `server.py`, `".fair_share"`)
- **Action required**: **test-only** — handler and routes are fully implemented

### Handler Dependencies
The handler uses 3 processor namespaces:
- `processors.fair_share` — domain/project/user fair share CRUD
- `processors.resource_usage` — usage bucket search
- `processors.scaling_group` — resource group spec get/search/update

### Auth Model
- **Global-scoped** endpoints (no `rg/` prefix): require `superadmin` via `_check_superadmin()`
- **RG-scoped** endpoints (`/rg/{rg}/...`): require auth only (`@auth_required_for_method`), no superadmin check

## Test Scenarios

### Component Tests (`tests/component/fair_share/`)

#### TestGetDomainFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_get_domain_fair_share` | Superadmin GET single domain fair share | - |
| `test_user_get_domain_fair_share_forbidden` | Regular user denied (403) | - |

#### TestSearchDomainFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_domain_fair_shares` | Superadmin POST search (empty result is valid) | - |
| `test_user_search_domain_fair_shares_forbidden` | Regular user denied (403) | - |

#### TestGetProjectFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_get_project_fair_share` | Superadmin GET single project fair share | - |
| `test_user_get_project_fair_share_forbidden` | Regular user denied (403) | - |

#### TestSearchProjectFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_project_fair_shares` | Superadmin POST search | - |

#### TestGetUserFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_get_user_fair_share` | Superadmin GET single user fair share | - |
| `test_user_get_user_fair_share_forbidden` | Regular user denied (403) | - |

#### TestSearchUserFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_user_fair_shares` | Superadmin POST search | - |

#### TestSearchDomainUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_domain_usage_buckets` | Superadmin POST search | - |

#### TestSearchProjectUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_project_usage_buckets` | Superadmin POST search | - |

#### TestSearchUserUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_user_usage_buckets` | Superadmin POST search | - |

#### TestRGGetDomainFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_get_domain_fair_share` | RG-scoped GET domain fair share | - |
| `test_user_rg_get_domain_fair_share` | Regular user can also access RG-scoped | - |

#### TestRGSearchDomainFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_domain_fair_shares` | RG-scoped POST search | - |

#### TestRGGetProjectFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_get_project_fair_share` | RG-scoped GET project fair share | - |

#### TestRGSearchProjectFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_project_fair_shares` | RG-scoped POST search | - |

#### TestRGGetUserFairShare
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_get_user_fair_share` | RG-scoped GET user fair share | - |

#### TestRGSearchUserFairShares
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_user_fair_shares` | RG-scoped POST search | - |

#### TestRGSearchDomainUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_domain_usage_buckets` | RG-scoped POST search | - |

#### TestRGSearchProjectUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_project_usage_buckets` | RG-scoped POST search | - |

#### TestRGSearchUserUsageBuckets
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_rg_search_user_usage_buckets` | RG-scoped POST search | - |

#### TestUpsertDomainFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_upsert_domain_weight` | Superadmin PUT weight | - |
| `test_user_upsert_domain_weight_forbidden` | Regular user denied (403) | - |

#### TestUpsertProjectFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_upsert_project_weight` | Superadmin PUT weight | - |

#### TestUpsertUserFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_upsert_user_weight` | Superadmin PUT weight | - |

#### TestBulkUpsertDomainFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_bulk_upsert_domain_weight` | Superadmin POST bulk upsert | - |

#### TestBulkUpsertProjectFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_bulk_upsert_project_weight` | Superadmin POST bulk upsert | - |

#### TestBulkUpsertUserFairShareWeight
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_bulk_upsert_user_weight` | Superadmin POST bulk upsert | - |

#### TestGetResourceGroupFairShareSpec
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_get_rg_spec` | Superadmin GET spec | - |
| `test_user_get_rg_spec_forbidden` | Regular user denied (403) | - |

#### TestSearchResourceGroupFairShareSpecs
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_search_rg_specs` | Superadmin GET all specs | - |

#### TestUpdateResourceGroupFairShareSpec
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_update_rg_spec` | Superadmin PATCH spec | - |

### Integration Tests (`tests/integration/fair_share/`)

| Test Class | Scenario |
|------------|----------|
| `TestFairShareWeightLifecycle` | upsert domain weight → get domain fair share → search → verify weight present |
| `TestFairShareBulkUpsertLifecycle` | bulk upsert domain weights → search → verify all present |
| `TestResourceGroupSpecLifecycle` | get RG spec → update spec → get again → verify updated |
| `TestRGScopedFairShareAccess` | RG-scoped get/search for domain/project/user (auth-only access) |

## Deferred Items

| Item | Reason |
|------|--------|
| _None_ | All 27 SDK methods map to standard HTTP handlers; no WebSocket/SSE endpoints |

## xfail Summary

**No xfail needed.** All SDK methods use either:
- **GET with path params only** (no query params) — HMAC bug does not apply
- **POST/PUT/PATCH with JSON body** — no query param issue

None of the methods send GET with query params or GET with JSON body, so neither known SDK bug applies.

## conftest.py Design

### `server_subapp_pkgs`
```python
[".auth", ".fair_share"]
```

### `server_cleanup_contexts`
Same as ACL/scaling_group pattern:
```python
[redis_ctx, database_ctx, monitoring_ctx, storage_manager_ctx,
 message_queue_ctx, event_producer_ctx, event_hub_ctx,
 background_task_ctx, _fair_share_domain_ctx]
```

### `_fair_share_domain_ctx`
Identical structure to ACL conftest: creates `Repositories` + `Processors` with real DB/Valkey clients and MagicMock for agent_registry and other infra-only components.

**Static import trick**: Must import `fair_share` API module for Pants PEX inclusion:
```python
from ai.backend.manager.api import fair_share as _fair_share_api
```

## Implementation Steps

1. Create `tests/component/fair_share/__init__.py`
2. Create `tests/component/fair_share/conftest.py` (based on ACL pattern)
3. Create `tests/component/fair_share/test_fair_share.py` (all component test scenarios)
4. Create `tests/component/fair_share/BUILD` (`python_tests()`)
5. Create `tests/integration/fair_share/__init__.py`
6. Create `tests/integration/fair_share/conftest.py`
7. Create `tests/integration/fair_share/test_fair_share.py` (lifecycle integration tests)
8. Create `tests/integration/fair_share/BUILD` (`python_tests()`)
9. `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
