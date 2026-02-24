# Implementation Plan: BA-4590

## SDK v2 Client Analysis

**File**: `src/ai/backend/client/v2/domains/auto_scaling_rule.py`

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `create(request)` | POST | `/admin/auto-scaling-rules` | JSON body (`CreateAutoScalingRuleRequest`) | Returns `CreateAutoScalingRuleResponse` |
| `get(rule_id)` | GET | `/admin/auto-scaling-rules/{rule_id}` | Path param only | Returns `GetAutoScalingRuleResponse` |
| `search(request)` | POST | `/admin/auto-scaling-rules/search` | JSON body (`SearchAutoScalingRulesRequest`) | Pagination support |
| `update(rule_id, request)` | PATCH | `/admin/auto-scaling-rules/{rule_id}` | Path param + JSON body (`UpdateAutoScalingRuleRequest`) | Returns `UpdateAutoScalingRuleResponse` |
| `delete(request)` | POST | `/admin/auto-scaling-rules/delete` | JSON body (`DeleteAutoScalingRuleRequest`) | Returns `DeleteAutoScalingRuleResponse` |

**Key observation**: No methods use query params. All data is passed via JSON body or path params. This means **no HMAC signing bug** and **no GET JSON body bug** apply.

### Request DTOs

- `CreateAutoScalingRuleRequest`: model_deployment_id (UUID), metric_source (enum), metric_name (str), min_threshold (Decimal?), max_threshold (Decimal?), step_size (int), time_window (int), min_replicas (int?), max_replicas (int?)
- `SearchAutoScalingRulesRequest`: filter (by model_deployment_id?), order (created_at asc/desc), limit (1-1000, default 50), offset (default 0)
- `UpdateAutoScalingRuleRequest`: all fields optional (metric_source, metric_name, min/max_threshold, step_size, time_window, min/max_replicas)
- `DeleteAutoScalingRuleRequest`: rule_id (UUID)

## Server Handler Status

- **Handler package**: EXISTS at `src/ai/backend/manager/api/auto_scaling_rule/` (handler.py, adapter.py, __init__.py)
- **Registered in `global_subapp_pkgs`**: **NO** — missing from the list in `src/ai/backend/manager/server.py:331-370`
- **Action required**: **Register `.auto_scaling_rule` in `global_subapp_pkgs` + write tests**

### Handler Architecture

The handler uses `processors.deployment` (a `DeploymentProcessors` instance) which goes through:
```
Handler → DeploymentProcessors → DeploymentService → DeploymentRepository → DeploymentDBSource → DB
```

This is different from simpler domains (like scaling_group) where the service uses `Repositories.create()`.
The `DeploymentRepository` is normally injected from `DeploymentController._deployment_repository`, which in the standard scaling_group conftest pattern is `MagicMock()`.

**Challenge**: With `deployment_controller=MagicMock()`, the `_deployment_repository` attribute is also a MagicMock.
Service methods (`await self._deployment_repository.create_model_deployment_autoscaling_rule(...)`) would fail because MagicMock is not awaitable.

**Solution**: In the component test conftest, manually create a real `DeploymentRepository` using the test DB's `root_ctx.db` and `root_ctx.storage_manager`, then create a real `DeploymentService` + `DeploymentProcessors` and override `root_ctx.processors.deployment`.

### DB Dependencies

- **Table**: `endpoint_auto_scaling_rules` (FK → `endpoints.id` ON DELETE CASCADE)
- **Endpoint table**: `endpoints` requires FKs to `domains.name`, `groups.id`, `scaling_groups.name`, and `created_user`/`session_owner` UUIDs (users), `image` (images)
- **Fixture approach**: Insert a minimal `EndpointRow` using raw SQL or ORM in a fixture, leveraging existing DB fixture data (default domain, default group, default user, default scaling group from `database_fixture`)

## Test Scenarios

### Component Tests (`tests/component/auto_scaling_rule/`)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestAutoScalingRuleCreate` | `test_admin_creates_rule` | Admin creates a rule with max_threshold → 201 | - |
| `TestAutoScalingRuleCreate` | `test_admin_creates_rule_with_min_threshold` | Admin creates a rule with min_threshold only → 201 | - |
| `TestAutoScalingRuleCreate` | `test_create_with_nonexistent_deployment` | Create rule for non-existent deployment → error | - |
| `TestAutoScalingRuleGet` | `test_admin_gets_rule` | Admin gets a created rule by ID → 200 | - |
| `TestAutoScalingRuleGet` | `test_get_nonexistent_rule` | Get rule with random UUID → 404 | - |
| `TestAutoScalingRuleSearch` | `test_admin_searches_rules` | Search all rules → paginated response | - |
| `TestAutoScalingRuleSearch` | `test_search_with_deployment_filter` | Search with model_deployment_id filter | - |
| `TestAutoScalingRuleSearch` | `test_search_empty_result` | Search with non-matching filter → empty list | - |
| `TestAutoScalingRuleUpdate` | `test_admin_updates_rule` | Update metric_name and step_size → 200 | - |
| `TestAutoScalingRuleUpdate` | `test_update_nonexistent_rule` | Update non-existent rule → 404 | - |
| `TestAutoScalingRuleDelete` | `test_admin_deletes_rule` | Delete an existing rule → deleted=true | - |
| `TestAutoScalingRuleDelete` | `test_delete_nonexistent_rule` | Delete non-existent rule → error | - |

### Integration Tests (`tests/integration/auto_scaling_rule/`)

| Test Class | Scenario |
|------------|----------|
| `TestAutoScalingRuleLifecycle` | create → get → update → get (verify update) → search → delete → get (verify 404) |

## Deferred Items

| Item | Reason |
|------|--------|
| Non-admin user access tests | All endpoints are under `/admin/` prefix → admin-only by design |
| WebSocket/streaming | No streaming endpoints in this domain |

## Implementation Steps

1. **Register handler**: Add `".auto_scaling_rule"` to `global_subapp_pkgs` in `src/ai/backend/manager/server.py`
2. **Create `tests/component/auto_scaling_rule/__init__.py`** (empty)
3. **Create `tests/component/auto_scaling_rule/conftest.py`**:
   - Override `server_subapp_pkgs` → `[".auth", ".auto_scaling_rule"]`
   - Override `server_cleanup_contexts` with standard contexts + `_auto_scaling_rule_domain_ctx`
   - `_auto_scaling_rule_domain_ctx`: Create real `Repositories`, create real `DeploymentRepository` (using `root_ctx.db`, `root_ctx.storage_manager`, valkey clients), create `DeploymentService` with MagicMock controller + real repo, create `DeploymentProcessors`, override `root_ctx.processors.deployment`
   - `model_deployment_fixture`: Insert minimal `EndpointRow` into DB (using existing default domain/group/user/scaling_group from `database_fixture`)
4. **Create `tests/component/auto_scaling_rule/test_auto_scaling_rule.py`**: All component test scenarios
5. **Create `tests/component/auto_scaling_rule/BUILD`**: `python_tests()`
6. **Create `tests/integration/auto_scaling_rule/__init__.py`** (empty)
7. **Create `tests/integration/auto_scaling_rule/conftest.py`**: Integration-level conftest (minimal, leverages shared integration fixtures)
8. **Create `tests/integration/auto_scaling_rule/test_auto_scaling_rule.py`**: Lifecycle integration test
9. **Create `tests/integration/auto_scaling_rule/BUILD`**: `python_tests()`
10. **Run `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`**
11. **PR + changelog**

## Key Technical Decisions

### conftest: Real DeploymentRepository vs MagicMock

The standard pattern (`deployment_controller=MagicMock()`) doesn't work here because:
- `DeploymentService.__init__` stores `deployment_controller._deployment_repository` (which is another MagicMock)
- Service methods `await self._deployment_repository.create_...()` fail because MagicMock isn't awaitable

Solution: Create a real `DeploymentRepository` in the domain context:
```python
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

deployment_repo = DeploymentRepository(
    db=root_ctx.db,
    storage_manager=root_ctx.storage_manager,
    valkey_stat=root_ctx.valkey_stat,
    valkey_live=root_ctx.valkey_live,
    valkey_schedule=root_ctx.valkey_schedule,
)
```

Then create `DeploymentService(MagicMock(), deployment_repo)` and wire up `DeploymentProcessors`.

### EndpointRow Fixture

The `endpoints` table has FKs to `domains`, `groups`, `scaling_groups`, and references `users`. The test DB `database_fixture` already provides default entries for these. We need a fixture that inserts a minimal `EndpointRow` with:
- `name`: test endpoint name
- `created_user` / `session_owner`: default admin user UUID
- `domain`: "default" (from database_fixture)
- `project`: default group UUID (from database_fixture)
- `resource_group`: default scaling group name (from database_fixture)
- `image`: default image UUID (from database_fixture)
- `resource_slots`: minimal `{"cpu": "1", "mem": "1073741824"}`
- `lifecycle_stage`: `EndpointLifecycle.CREATED`

> **image FK note**: Verify whether `database_fixture` seeds an `images` row. If it does, query the UUID and pass it to `EndpointRow`. If it does not, add a dedicated `image_fixture` pytest fixture in conftest.py that inserts a minimal `ImageRow` — do not use runtime conditional logic inside `model_deployment_fixture`.
