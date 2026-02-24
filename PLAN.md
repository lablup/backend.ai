# Implementation Plan: BA-4571

> **Plan status**: Complete — xfail markers correctly specified for all HMAC-affected tests. Integration tests scoped to avoid query param operations. Ready to implement.

## SDK v2 Client Analysis

**File:** `src/ai/backend/client/v2/domains/template.py` — `TemplateClient`

### Session Template Methods

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `create_session_template(request)` | POST | `/template/session` | JSON body | `model_dump(exclude_none=True)` as json |
| `list_session_templates(request)` | GET | `/template/session` | query params | Always sends `all=False` at minimum |
| `get_session_template(template_id, request?)` | GET | `/template/session/{template_id}` | query params (optional) | params=None if request omitted |
| `update_session_template(template_id, request)` | PUT | `/template/session/{template_id}` | JSON body | via `typed_request` |
| `delete_session_template(template_id, request?)` | DELETE | `/template/session/{template_id}` | query params (optional) | params=None if request omitted |

### Cluster Template Methods

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `create_cluster_template(request)` | POST | `/template/cluster` | JSON body | via `typed_request` |
| `list_cluster_templates(request)` | GET | `/template/cluster` | query params | Always sends `all=False` at minimum |
| `get_cluster_template(template_id, request?)` | GET | `/template/cluster/{template_id}` | query params (optional) | params=None if request omitted |
| `update_cluster_template(template_id, request)` | PUT | `/template/cluster/{template_id}` | JSON body | via `typed_request` |
| `delete_cluster_template(template_id, request?)` | DELETE | `/template/cluster/{template_id}` | query params (optional) | params=None if request omitted |

## Server Handler Status

- **Session template handler:** EXISTS at `src/ai/backend/manager/api/session_template.py` (single-file module)
- **Cluster template handler:** EXISTS at `src/ai/backend/manager/api/cluster_template.py` (single-file module)
- **Registered in `global_subapp_pkgs`:** YES — both `.cluster_template` and `.session_template` (server.py:349-350)
- **Action required:** test-only (no handler implementation needed)

### Handler Details

Both handlers use the legacy `@check_api_params` pattern with trafaret validation. Key behavior from `check_api_params`:
- **GET/HEAD**: reads params from `dict(request.query)` (query string)
- **POST/PUT/DELETE**: reads params from `request.text()` (request body, JSON or YAML)

This means:
- `list_*` (GET with query params) → server reads from query ✓, but HMAC signing bug causes 401
- `get_*` without request param (GET, no query params) → server uses trafaret defaults ✓
- `get_*` with request param (GET, query params) → HMAC signing bug causes 401
- `create_*` / `update_*` (POST/PUT with JSON body) → server reads from body ✓
- `delete_*` without request param (DELETE, no body/params) → server reads empty query, uses trafaret defaults ✓
- `delete_*` with request param containing owner_access_key → HMAC bug if non-empty query params

### Template Payload Structure

**Session template** (`check_task_template` via `task_template_v1` trafaret):
```json
[{
  "name": "test-template",
  "template": {
    "apiVersion": "v1",
    "kind": "taskTemplate",
    "metadata": {"name": "test-template"},
    "spec": {
      "kernel": {"image": "cr.backend.ai/testing/python:3.9"}
    }
  }
}]
```

**Cluster template** (`check_cluster_template` via `cluster_template_v1` trafaret):
```json
{
  "name": "test-cluster",
  "template": {
    "apiVersion": "v1",
    "kind": "clusterTemplate",
    "mode": "single-node",
    "metadata": {"name": "test-cluster"},
    "spec": {
      "nodes": [
        {"role": "default", "session_template": "<uuid-of-session-template>", "replicas": 1}
      ]
    }
  }
}
```

Note: Cluster template creation requires a pre-existing session template UUID for the `session_template` field in nodes.

## Test Scenarios

### Component Tests (`tests/component/template/`)

#### Session Template Tests

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestCreateSessionTemplate` | `test_admin_creates_session_template` | Admin creates a session template via POST | - |
| `TestCreateSessionTemplate` | `test_user_creates_session_template` | Regular user creates a session template | - |
| `TestGetSessionTemplate` | `test_admin_gets_session_template` | Admin retrieves template by ID (no query params) | - |
| `TestGetSessionTemplate` | `test_user_gets_session_template` | Regular user retrieves template by ID | - |
| `TestGetSessionTemplate` | `test_get_with_format_param` | GET with format query param | xfail: HMAC bug |
| `TestListSessionTemplates` | `test_list_session_templates` | List templates (GET with query params) | xfail: HMAC bug |
| `TestUpdateSessionTemplate` | `test_admin_updates_session_template` | Admin updates template via PUT | - |
| `TestDeleteSessionTemplate` | `test_admin_deletes_session_template` | Admin deletes template (no query params) | - |
| `TestDeleteSessionTemplate` | `test_get_deleted_template_returns_empty` | Verify soft-deleted template is not retrievable | - |

#### Cluster Template Tests

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestCreateClusterTemplate` | `test_admin_creates_cluster_template` | Admin creates cluster template (requires session template first) | - |
| `TestGetClusterTemplate` | `test_admin_gets_cluster_template` | Admin retrieves cluster template by ID (no query params) | - |
| `TestGetClusterTemplate` | `test_get_with_format_param` | GET with format query param | xfail: HMAC bug |
| `TestListClusterTemplates` | `test_list_cluster_templates` | List cluster templates (GET with query params) | xfail: HMAC bug |
| `TestUpdateClusterTemplate` | `test_admin_updates_cluster_template` | Admin updates cluster template via PUT | - |
| `TestDeleteClusterTemplate` | `test_admin_deletes_cluster_template` | Admin deletes cluster template (no query params) | - |

### Integration Tests (`tests/integration/template/`)

| Test Class | Test Method | Scenario |
|------------|-------------|----------|
| `TestSessionTemplateLifecycle` | `test_create_get_update_delete` | Full CRUD lifecycle: create → get → update → get → delete → verify gone |
| `TestClusterTemplateLifecycle` | `test_create_get_update_delete` | Full CRUD: create session template → create cluster template → get → update → delete |

Note: Integration tests also subject to HMAC bug for list/get-with-params — lifecycle tests use only non-query-param operations.

## Deferred Items

| Item | Reason |
|------|--------|
| List with `all=True` (superadmin-only) | HMAC signing bug on all GET query params |
| List with `group_id` filter | HMAC signing bug on all GET query params |
| Get with `format=yaml` | HMAC signing bug when passing query params |
| Delete with `owner_access_key` | HMAC signing bug when passing query params |
| Multi-template create (array payload) | Complex setup; covered by single-create tests |

## xfail Markers

All xfail tests use:
```python
@pytest.mark.xfail(
    strict=True,
    reason="Client SDK v2 HMAC signing omits query params; server verifies against request.raw_path (including ?param=...). Endpoints passing query params cause 401.",
)
```

## Implementation Steps

1. Create `tests/component/template/__init__.py`
2. Create `tests/component/template/conftest.py`
   - `server_subapp_pkgs()` → `[".auth", ".session_template", ".cluster_template"]`
   - `server_cleanup_contexts()` → same as ACL reference (redis, db, monitoring, storage_manager, message_queue, event_producer, event_hub, background_task, domain_ctx)
   - `_template_domain_ctx(root_ctx)` → Repositories + Processors init
   - Static imports for `session_template` and `cluster_template` API modules
3. Create `tests/component/template/test_template.py`
   - Session template: create, get, update, delete (happy path) + list, get-with-format (xfail)
   - Cluster template: create, get, update, delete (happy path) + list, get-with-format (xfail)
4. Create `tests/component/template/BUILD` → `python_tests()`
5. Create `tests/integration/template/__init__.py`
6. Create `tests/integration/template/conftest.py` (minimal, inherits from parent)
7. Create `tests/integration/template/test_template.py`
   - Session template lifecycle
   - Cluster template lifecycle (depends on session template)
8. Create `tests/integration/template/BUILD` → `python_tests()`
9. Run `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
