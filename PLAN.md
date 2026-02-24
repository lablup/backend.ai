# Implementation Plan: BA-4583

## SDK v2 Client Analysis

**File:** `src/ai/backend/client/v2/domains/error_log.py`
**Class:** `ErrorLogClient(BaseDomainClient)` — `API_PREFIX = "/logs/error"`

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `append(request)` | POST | `/logs/error` | JSON body | Creates a new error log entry |
| `list_logs(request=None)` | GET | `/logs/error` | query params (when request provided) | Pagination + mark_read |
| `mark_cleared(log_id)` | POST | `/logs/error/{log_id}/clear` | path param (log_id) | Marks log as cleared |

### Request/Response DTOs

**AppendErrorLogRequest:** severity, source, message, context_lang, context_env, request_url?, request_status?, traceback?
**ListErrorLogsRequest:** mark_read (default=False), page_size (default=20, 1-100), page_no (default=1)
**AppendErrorLogResponse:** success (bool)
**ListErrorLogsResponse:** logs (list[ErrorLogDTO]), count (int)
**MarkClearedResponse:** success (bool)
**ErrorLogDTO:** log_id, created_at, severity, source, user?, is_read, message, context_lang, context_env, request_url?, request_status?, traceback?, is_cleared? (admin only)

## Server Handler Status

- **Handler module:** EXISTS at `src/ai/backend/manager/api/logs.py`
- **Registered in global_subapp_pkgs:** YES — `".logs"` (server.py line 356)
- **App prefix:** `"logs/error"` (logs.py line 276)
- **Action required:** test-only (no handler implementation needed)

### Handler Details
- `append()` — `@server_status_required(READ_ALLOWED)` + `@auth_required` + `@check_api_params`
  - Uses `ErrorLogProcessors.create` via `root_ctx.processors.error_log.create`
- `list_logs()` — `@auth_required` + `@server_status_required(READ_ALLOWED)` + `@check_api_params`
  - Direct SQL (not using Processors), role-based filtering (superadmin/admin/user)
  - For GET: `check_api_params` reads from `request.query` (utils.py line 195-202)
- `mark_cleared()` — `@auth_required` + `@server_status_required(READ_ALLOWED)`
  - Direct SQL, role-based access control, no `@check_api_params`
- **Lifecycle hooks:** `init()` registers `GlobalTimer` for log cleanup using `event_dispatcher.consume()` — requires mock

## xfail Bug Analysis

### HMAC Query Param Bug
- **Affected method:** `list_logs(request=ListErrorLogsRequest(...))`
- **Mechanism:** SDK signs path `/logs/error`, server verifies `request.raw_path` = `/logs/error?mark_read=False&page_size=20&page_no=1`
- **Result:** 401 Unauthorized
- **Safe variant:** `list_logs()` with `request=None` sends no query params — HMAC matches

### GET JSON Body Bug
- **Not applicable:** `list_logs` correctly uses `params=` (query params), not JSON body

## Test Scenarios

### Component Tests (`tests/component/error_log/`)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestAppendErrorLog` | `test_admin_appends_error_log` | Superadmin creates error log with all fields | - |
| `TestAppendErrorLog` | `test_admin_appends_error_log_minimal` | Superadmin creates error log with required fields only | - |
| `TestAppendErrorLog` | `test_user_appends_error_log` | Regular user creates error log | - |
| `TestListErrorLogs` | `test_admin_lists_error_logs` | Superadmin lists logs (no query params) | - |
| `TestListErrorLogs` | `test_user_lists_own_error_logs` | Regular user lists only own logs (no query params) | - |
| `TestListErrorLogs` | `test_list_logs_with_query_params` | List with explicit pagination params | HMAC bug |
| `TestListErrorLogs` | `test_list_logs_with_mark_read` | List with mark_read=True | HMAC bug |
| `TestMarkCleared` | `test_admin_marks_log_cleared` | Superadmin clears a specific log | - |
| `TestMarkCleared` | `test_user_marks_own_log_cleared` | Regular user clears own log | - |

### Integration Tests (`tests/integration/error_log/`)

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestErrorLogLifecycle` | `test_append_list_clear_lifecycle` | append → list (default) → verify log present → mark_cleared → list → verify cleared (admin) | - |
| `TestErrorLogLifecycle` | `test_user_sees_only_own_logs` | user1 appends → user2 appends → user1 lists → only sees own | - |
| `TestErrorLogLifecycle` | `test_list_with_pagination_params` | append multiple → list with page_size/page_no | HMAC bug |

## Deferred Items

| Item | Reason |
|------|--------|
| `log_cleanup_task` | Background timer task; not directly testable via HTTP client |
| Domain admin role-based filtering | Requires multi-domain setup with group associations; complex fixture setup beyond scope |

## Implementation Steps

1. Create `tests/component/error_log/__init__.py`
2. Create `tests/component/error_log/conftest.py`
   - Static imports: `_auth_api`, `_logs_api` (for Pants)
   - `_error_log_domain_ctx()` context manager (Repositories + Processors + mock event_dispatcher)
   - `server_subapp_pkgs()` → `[".auth", ".logs"]`
   - `server_cleanup_contexts()` → standard contexts + `_error_log_domain_ctx`
3. Create `tests/component/error_log/test_error_log.py`
   - `TestAppendErrorLog` (3 tests)
   - `TestListErrorLogs` (4 tests, 2 xfail)
   - `TestMarkCleared` (2 tests)
4. Create `tests/component/error_log/BUILD` → `python_tests()`
5. Create `tests/integration/error_log/__init__.py`
6. Create `tests/integration/error_log/conftest.py`
   - Follow `tests/integration/auth/conftest.py` pattern
7. Create `tests/integration/error_log/test_error_log.py`
   - `TestErrorLogLifecycle` (3 tests, 1 xfail)
8. Create `tests/integration/error_log/BUILD` → `python_tests()`
9. `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
