# Implementation Plan: BA-4568

## SDK v2 Client Analysis

**File**: `src/ai/backend/client/v2/domains/deployment.py`
**Class**: `DeploymentClient` (extends `BaseDomainClient`, `API_PREFIX = "/deployments"`)

### Deployment CRUD
| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `create_deployment(request)` | POST | `/deployments` | JSON body (`CreateDeploymentRequest`) | Complex: needs image, vfolder, scaling_group |
| `search_deployments(request)` | POST | `/deployments/search` | JSON body (`SearchDeploymentsRequest`) | Filter/order/pagination |
| `get_deployment(deployment_id)` | GET | `/deployments/{deployment_id}` | Path param only | No query params → no HMAC bug |
| `update_deployment(deployment_id, request)` | PATCH | `/deployments/{deployment_id}` | Path param + JSON body (`UpdateDeploymentRequest`) | name, desired_replicas |
| `destroy_deployment(deployment_id)` | DELETE | `/deployments/{deployment_id}` | Path param only | |

### Revision Operations
| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `create_revision(deployment_id, request)` | POST | `/deployments/{deployment_id}/revisions` | Path param + JSON body (`CreateRevisionRequest`) | Needs image, vfolder |
| `search_revisions(deployment_id, request)` | POST | `/deployments/{deployment_id}/revisions/search` | Path param + JSON body (`SearchRevisionsRequest`) | Filter by deployment_id injected |
| `get_revision(deployment_id, revision_id)` | GET | `/deployments/{deployment_id}/revisions/{revision_id}` | Path params only | No HMAC bug |
| `activate_revision(deployment_id, revision_id)` | POST | `/deployments/{deployment_id}/revisions/{revision_id}/activate` | Path params only | Triggers scheduling |
| `deactivate_revision(deployment_id, revision_id)` | POST | `/deployments/{deployment_id}/revisions/{revision_id}/deactivate` | Path params only | **Stub**: always returns success=True |

### Route Operations
| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `search_routes(deployment_id, request)` | POST | `/deployments/{deployment_id}/routes/search` | Path param + JSON body (`SearchRoutesRequest`) | Cursor pagination |
| `update_route_traffic_status(deployment_id, route_id, request)` | PATCH | `/deployments/{deployment_id}/routes/{route_id}/traffic-status` | Path params + JSON body | |

**Total: 12 SDK methods**

## Server Handler Status

- **Handler package**: EXISTS at `src/ai/backend/manager/api/deployment/handler.py`
  - `DeploymentAPIHandler` class with all 12 endpoints
  - `create_app()` registered at `app["prefix"] = "deployments"`, `api_versions = (4, 5)`
  - Adapter layer: `src/ai/backend/manager/api/deployment/adapter.py`
- **Registered in `global_subapp_pkgs`**: YES (line 360 of `server.py`)
- **Action required**: **test-only** (handler fully implemented)

## Known SDK Bug Assessment

| Bug | Applies? | Reason |
|-----|----------|--------|
| HMAC query param bug | **NO** | All GET endpoints use path params only; search uses POST |
| GET JSON body bug | **NO** | GET endpoints have no body; search endpoints use POST |
| Streaming (WS/SSE) | **NO** | No streaming endpoints in deployment domain |

**All 12 methods are testable without xfail.**

## Test Scenarios

### Fixture: `deployment_factory` (DEFERRED)

> **Status**: DEFERRED — requires EndpointRow direct DB insertion with complex FK relationships
> (domain, project, user, image, scaling_group, deployment_policy). Tracked in Deferred Items below.

`EndpointRow`를 DB에 직접 삽입해 happy-path 테스트를 가능하게 한다. BA-4590의 `model_deployment_fixture`와 동일 접근법.

- `domain`: "default" (database_fixture 제공)
- `project`: default group UUID (database_fixture 제공)
- `created_user` / `session_owner`: default admin UUID (database_fixture 제공)
- `resource_group`: default scaling group name (database_fixture 제공)
- `image`: database_fixture에 image row가 있으면 그 UUID 사용; 없으면 conftest에 별도 `image_fixture` 추가
- `resource_slots`: `{"cpu": "1", "mem": "1073741824"}`
- `lifecycle_stage`: `EndpointLifecycle.CREATED`

### Component Tests (`tests/component/deployment/`)

#### TestSearchDeployments
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_search_deployments_empty` | Search with no data → empty list, pagination total=0 | - |
| `test_search_deployments_with_data` | deployment_factory로 시딩 후 search → 1건 포함된 결과 | - |
| `test_search_deployments_with_name_filter` | name 필터 일치/불일치 케이스 | - |

#### TestGetDeployment
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_get_deployment_not_found` | GET non-existent UUID → proper error response | - |
| `test_admin_gets_deployment` | deployment_factory 시딩 → GET → 필드 검증 | - |

#### TestUpdateDeployment (DEFERRED)

> **Status**: DEFERRED — depends on `deployment_factory` fixture. See Deferred Items.

| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_updates_deployment` | deployment_factory 시딩 → PATCH name/desired_replicas → 업데이트 반영 확인 | - |
| `test_update_nonexistent_deployment` | 존재하지 않는 UUID → error | - |

#### TestDestroyDeployment (DEFERRED)

> **Status**: DEFERRED — depends on `deployment_factory` fixture. See Deferred Items.

| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_admin_destroys_deployment` | deployment_factory 시딩 → DELETE → 이후 GET 시 not found | - |

#### TestSearchRevisions
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_search_revisions_empty` | Search revisions for non-existent deployment → empty or error | - |

#### TestDeactivateRevision
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_deactivate_revision_stub` | Deactivate always returns success=True (stub handler) | - |

#### TestSearchRoutes
| Test Method | Scenario | xfail? |
|-------------|----------|--------|
| `test_search_routes_empty` | Search routes for non-existent deployment → empty or error | - |

### Integration Tests (`tests/integration/deployment/`)

Integration tests require a full running manager with real infrastructure (agents, images, vfolders, scaling groups). These test the full lifecycle.

| Test Class | Scenario |
|------------|----------|
| `TestDeploymentLifecycle` | create → get → update → search → destroy |
| `TestRevisionLifecycle` | create deployment → create revision → get revision → search revisions |
| `TestRouteOperations` | create deployment → activate revision → search routes → update traffic status |

**Note**: Integration tests are deferred to when full test infrastructure (live agents, images, vfolders) is available. Creating the test skeleton with `pytest.mark.integration` is in scope.

## Deferred Items

| Item | Reason |
|------|--------|
| `deployment_factory` fixture | Requires EndpointRow direct DB insertion with complex FK relationships: domain, project, user, image, scaling_group, deployment_policy. Similar to BA-4590 `model_deployment_fixture`. |
| `create_deployment` component test | Requires extensive fixtures: valid domain, project, user, image, vfolder, scaling_group. Service layer calls deep into infrastructure (agent_registry, deployment_controller). |
| `update_deployment` component test | Needs `deployment_factory` fixture (depends on EndpointRow seeding) |
| `destroy_deployment` component test | Needs `deployment_factory` fixture (depends on EndpointRow seeding) |
| `create_revision` component test | Needs existing deployment + image + vfolder |
| `get_revision` component test | Needs existing revision (depends on create_revision) |
| `activate_revision` component test | Triggers real scheduling via deployment_controller (mocked but complex) |
| `update_route_traffic_status` component test | Needs existing route (created by activate_revision) |
| Full integration lifecycle tests | Requires live agent infrastructure not available in component test env |

## Implementation Steps

1. Create `tests/component/deployment/__init__.py`
2. Create `tests/component/deployment/conftest.py`
   - `server_subapp_pkgs()` → `[".auth", ".deployment"]`
   - `server_cleanup_contexts()` → same as ACL pattern
   - `_deployment_domain_ctx(root_ctx)` → Repositories + Processors init with mocks
   - `deployment_factory` fixture → EndpointRow DB 직접 삽입 (image FK 확인 후 image_fixture 필요 시 추가)
3. Create `tests/component/deployment/test_deployment.py`
   - `TestSearchDeployments` — empty + 데이터 있을 때 + name 필터
   - `TestGetDeployment` — not found + happy path (deployment_factory)
   - `TestUpdateDeployment` — happy path + not found
   - `TestDestroyDeployment` — happy path (deployment_factory)
   - `TestSearchRevisions` — empty
   - `TestDeactivateRevision` — stub handler always success
   - `TestSearchRoutes` — empty
4. Create `tests/component/deployment/BUILD` → `python_tests()`
5. Create `tests/integration/deployment/__init__.py`
6. Create `tests/integration/deployment/conftest.py` — minimal skeleton
7. Create `tests/integration/deployment/test_deployment.py` — lifecycle test skeletons with `pytest.mark.integration`
8. Create `tests/integration/deployment/BUILD` → `python_tests()`
9. Run `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
