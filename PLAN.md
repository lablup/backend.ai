# Implementation Plan: BA-4576

Add export domain test scenarios via Client SDK v2.

## SDK v2 Client Analysis

Source: `src/ai/backend/client/v2/domains/export.py` — `ExportClient(BaseDomainClient)`

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `list_reports()` | GET | `/export/reports` | none | Returns `ListExportReportsResponse` |
| `get_report(report_key)` | GET | `/export/reports/{report_key}` | path param | Returns `GetExportReportResponse` |
| `download_users_csv(request?)` | POST | `/export/users/csv` | JSON body (optional) | Returns `bytes` (streaming CSV) |
| `download_sessions_csv(request?)` | POST | `/export/sessions/csv` | JSON body (optional) | Returns `bytes` (streaming CSV) |
| `download_projects_csv(request?)` | POST | `/export/projects/csv` | JSON body (optional) | Returns `bytes` (streaming CSV) |
| `download_keypairs_csv(request?)` | POST | `/export/keypairs/csv` | JSON body (optional) | Returns `bytes` (streaming CSV) |
| `download_audit_logs_csv(request?)` | POST | `/export/audit-logs/csv` | JSON body (optional) | Returns `bytes` (streaming CSV) |

**Total: 7 methods**

### Key observations

- All CSV download methods use the client's `download()` helper which defaults to `method="POST"` with optional JSON body — **no HMAC query-param bug**.
- `list_reports()` and `get_report()` are simple GET endpoints with no query params — **no HMAC bug**.
- CSV endpoints use `stream_api_handler` returning `APIStreamResponse`. The SDK's `download()` calls `await resp.read()` which works fine over real HTTP.
- **All export endpoints require superadmin** — regular user requests return 403 Forbidden.
- CSV handlers depend on `ExportCtx` (resolves `root_ctx.repositories.export.repository` + `root_ctx.config_provider.config.export`).

## Server Handler Status

- **Handler package**: EXISTS at `src/ai/backend/manager/api/export/handler.py`
- **Registered in `global_subapp_pkgs`**: YES (`.export` at line 365 in `server.py`)
- **Processors wired**: YES (`ExportProcessors` in `Processors.create()`)
- **Action required**: test-only (no handler implementation needed)

### Handler route summary

| Route | Handler | Decorator |
|-------|---------|-----------|
| `GET /reports` | `ExportAPIHandler.list_reports` | `@api_handler` |
| `GET /reports/{report_key}` | `ExportAPIHandler.get_report` | `@api_handler` |
| `POST /users/csv` | `UserExportHandler.export_csv` | `@stream_api_handler` |
| `POST /sessions/csv` | `SessionExportHandler.export_csv` | `@stream_api_handler` |
| `POST /projects/csv` | `ProjectExportHandler.export_csv` | `@stream_api_handler` |
| `POST /keypairs/csv` | `KeypairExportHandler.export_csv` | `@stream_api_handler` |
| `POST /audit-logs/csv` | `AuditLogExportHandler.export_csv` | `@stream_api_handler` |

## Test Scenarios

### Component Tests (`tests/component/export/`)

#### conftest.py setup
- `server_subapp_pkgs`: `[".auth", ".export"]`
- `server_cleanup_contexts`: standard 8 contexts + `_export_domain_ctx`
- `_export_domain_ctx`: wires `Repositories` and `Processors` (same pattern as ACL)
- Static import: `from ai.backend.manager.api import export as _export_api`

#### Test file: `test_export.py`

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestListReports` | `test_admin_lists_reports` | Admin GET /export/reports — returns report list | - |
| `TestListReports` | `test_regular_user_forbidden` | Regular user GET /export/reports — 403 | - |
| `TestGetReport` | `test_admin_gets_users_report` | Admin GET /export/reports/users — returns report info | - |
| `TestGetReport` | `test_admin_gets_sessions_report` | Admin GET /export/reports/sessions — returns report info | - |
| `TestGetReport` | `test_admin_gets_projects_report` | Admin GET /export/reports/projects — returns report info | - |
| `TestGetReport` | `test_get_nonexistent_report` | Admin GET /export/reports/nonexistent — error | - |
| `TestGetReport` | `test_regular_user_forbidden` | Regular user GET /export/reports/users — 403 | - |
| `TestDownloadUsersCSV` | `test_admin_downloads_users_csv` | Admin POST /export/users/csv (no body) — CSV bytes | - |
| `TestDownloadUsersCSV` | `test_admin_downloads_with_fields` | Admin POST with `fields` filter — CSV with selected columns | - |
| `TestDownloadUsersCSV` | `test_regular_user_forbidden` | Regular user POST — 403 | - |
| `TestDownloadSessionsCSV` | `test_admin_downloads_sessions_csv` | Admin POST /export/sessions/csv — CSV bytes (may be empty) | - |
| `TestDownloadSessionsCSV` | `test_regular_user_forbidden` | Regular user POST — 403 | - |
| `TestDownloadProjectsCSV` | `test_admin_downloads_projects_csv` | Admin POST /export/projects/csv — CSV bytes | - |
| `TestDownloadProjectsCSV` | `test_regular_user_forbidden` | Regular user POST — 403 | - |
| `TestDownloadKeypairsCSV` | `test_admin_downloads_keypairs_csv` | Admin POST /export/keypairs/csv — CSV bytes | - |
| `TestDownloadKeypairsCSV` | `test_regular_user_forbidden` | Regular user POST — 403 | - |
| `TestDownloadAuditLogsCSV` | `test_admin_downloads_audit_logs_csv` | Admin POST /export/audit-logs/csv — CSV bytes (may be empty) | - |
| `TestDownloadAuditLogsCSV` | `test_regular_user_forbidden` | Regular user POST — 403 | - |

**Note on xfail**: No xfail markers needed — all endpoints use POST with JSON body (no HMAC query-param bug) or simple GET without query params.

### Integration Tests (`tests/integration/export/`)

Uses the integration conftest's `server_factory` fixture (full-stack manager with ALL cleanup contexts and ALL subapp packages).

#### conftest.py setup
- No fixture overrides needed — integration conftest already loads all subapps
- May add domain-specific data fixtures if needed

#### Test file: `test_export.py`

| Test Class | Scenario |
|------------|----------|
| `TestExportLifecycle` | `list_reports` → validate report keys → `get_report(key)` → validate fields |
| `TestExportCSVDownload` | `download_users_csv` → verify CSV headers/rows match seeded data |
| `TestExportCSVDownload` | `download_projects_csv` → verify CSV contains seeded group |
| `TestExportCSVDownload` | `download_keypairs_csv` → verify CSV contains seeded keypairs |
| `TestExportAccessControl` | regular user tries all export endpoints → all return 403 |

## Deferred Items

| Item | Reason |
|------|--------|
| CSV encoding (`euc-kr`) tests | Requires encoding-aware CSV parsing; low priority |
| Filter/order parameter combination tests | Complex test matrix; suitable for future fine-grained test PR |
| Concurrent export limit tests | Requires `max_concurrent_exports` config and concurrent requests |

## Implementation Steps

1. Create `tests/component/export/__init__.py` (empty)
2. Create `tests/component/export/conftest.py` (domain context + fixture overrides)
3. Create `tests/component/export/test_export.py` (18 test methods)
4. Create `tests/component/export/BUILD` (`python_tests()`)
5. Create `tests/integration/export/__init__.py` (empty)
6. Create `tests/integration/export/conftest.py` (minimal, inherits from integration conftest)
7. Create `tests/integration/export/test_export.py` (5 test methods)
8. Create `tests/integration/export/BUILD` (`python_tests()`)
9. `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
