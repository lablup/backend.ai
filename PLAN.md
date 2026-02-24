# Implementation Plan: BA-4586

## SDK v2 Client Analysis

**Client class**: `ArtifactClient` at `src/ai/backend/client/v2/domains/artifact.py`
**Registry accessor**: `admin_registry.artifact` (via `BackendAIClientRegistry`)
**API prefix**: `/artifacts`

| # | Method | HTTP | Endpoint | Params style | Notes |
|---|--------|------|----------|-------------|-------|
| 1 | `import_artifacts(request)` | POST | `/artifacts/import` | JSON body (`ImportArtifactsRequest`) | Triggers background download from external registry; returns task IDs |
| 2 | `update_artifact(artifact_id, request)` | PATCH | `/artifacts/{artifact_id}` | path + JSON body (`UpdateArtifactRequest`) | Updates metadata (readonly, description) |
| 3 | `cancel_import_task(request)` | POST | `/artifacts/task/cancel` | JSON body (`CancelImportTaskRequest`) | Cancels an active import task |
| 4 | `cleanup_revisions(request)` | POST | `/artifacts/revisions/cleanup` | JSON body (`CleanupRevisionsRequest`) | Removes downloaded files, reverts to SCANNED status |
| 5 | `approve_revision(artifact_revision_id)` | POST | `/artifacts/revisions/{id}/approval` | path param only | Admin approves a revision |
| 6 | `reject_revision(artifact_revision_id)` | POST | `/artifacts/revisions/{id}/rejection` | path param only | Admin rejects a revision |
| 7 | `get_revision_readme(artifact_revision_id)` | GET | `/artifacts/revisions/{id}/readme` | path param only | Reads README from storage |
| 8 | `get_revision_verification_result(artifact_revision_id)` | GET | `/artifacts/revisions/{id}/verification-result` | path param only | Reads verification result from storage |
| 9 | `get_revision_download_progress(artifact_revision_id)` | GET | `/artifacts/revisions/{id}/download-progress` | path param only | Reads download progress from Redis/storage |

**HMAC/Query param bug**: Not applicable — no method uses query params.
**GET JSON body bug**: Not applicable — all GET methods use path params only.

## Server Handler Status

- **Handler file**: EXISTS at `src/ai/backend/manager/api/artifact.py` (single file, not a package)
- **Registered in `global_subapp_pkgs`**: YES (`.artifact` at line ~333 of `server.py`)
- **Route table** (in `create_app()`):
  - `POST /revisions/cleanup` → `cleanup_artifacts`
  - `POST /revisions/{artifact_revision_id}/approval` → `approve_artifact_revision`
  - `POST /revisions/{artifact_revision_id}/rejection` → `reject_artifact_revision`
  - `POST /task/cancel` → `cancel_import_artifact`
  - `POST /import` → `import_artifacts`
  - `PATCH /{artifact_id}` → `update_artifact`
  - `GET /revisions/{artifact_revision_id}/readme` → `get_artifact_revision_readme`
  - `GET /revisions/{artifact_revision_id}/verification-result` → `get_artifact_revision_verification_result`
  - `GET /revisions/{artifact_revision_id}/download-progress` → `get_download_progress`
- **Action required**: test-only (handler already fully implemented)

## DB Models Required for Fixtures

- `ArtifactRegistryRow` (`src/ai/backend/manager/models/artifact_registries/row.py`) — parent FK for artifacts
- `ArtifactRow` (`src/ai/backend/manager/models/artifact/row.py`) — parent FK for revisions
- `ArtifactRevisionRow` (`src/ai/backend/manager/models/artifact_revision/row.py`) — needed for revision operations

## Testability Assessment per Method

| Method | DB-only? | Storage-proxy needed? | Testability in component tests |
|--------|----------|----------------------|-------------------------------|
| `update_artifact` | Yes | No | HIGH — pure metadata update |
| `approve_revision` | Mostly | Depends on action impl | MEDIUM — status transition in DB |
| `reject_revision` | Mostly | Depends on action impl | MEDIUM — status transition in DB |
| `import_artifacts` | No | Yes (downloads files) | LOW — needs real registry + storage |
| `cancel_import_task` | No | Yes (needs active import) | LOW — requires running import task |
| `cleanup_revisions` | No | Yes (deletes files) | LOW — interacts with storage |
| `get_revision_readme` | No | Yes (reads from storage) | LOW — reads file from storage backend |
| `get_revision_verification_result` | Partially | Yes (reads from storage) | LOW — reads verification data |
| `get_revision_download_progress` | No | Yes (reads from Redis/storage) | LOW — reads progress from Redis |

## Test Scenarios

### Component Tests (`tests/component/artifact/`)

| Test Class | Test Method | Scenario | xfail? | Reason |
|------------|-------------|----------|--------|--------|
| `TestUpdateArtifact` | `test_admin_updates_artifact` | Admin updates artifact metadata (readonly, description) | - | DB-only operation |
| `TestUpdateArtifact` | `test_update_nonexistent_artifact` | Update with invalid UUID returns error | - | Error path |
| `TestApproveRevision` | `test_admin_approves_revision` | Admin approves an artifact revision | xfail | Action may interact with storage to verify revision state |
| `TestRejectRevision` | `test_admin_rejects_revision` | Admin rejects an artifact revision | xfail | Action may interact with storage to verify revision state |
| `TestImportArtifacts` | `test_admin_imports_artifacts` | Admin triggers artifact import | xfail | Requires real storage-proxy + external registry connection |
| `TestCancelImportTask` | `test_admin_cancels_import_task` | Admin cancels an active import | xfail | Requires active import task with storage-proxy |
| `TestCleanupRevisions` | `test_admin_cleans_up_revisions` | Admin cleans up artifact revision files | xfail | Interacts with storage-proxy to delete files |
| `TestGetRevisionReadme` | `test_admin_gets_revision_readme` | Admin retrieves revision README | xfail | Reads file content from storage backend |
| `TestGetRevisionVerificationResult` | `test_admin_gets_verification_result` | Admin retrieves revision verification result | xfail | Reads verification data from storage |
| `TestGetRevisionDownloadProgress` | `test_admin_gets_download_progress` | Admin retrieves revision download progress | xfail | Reads progress data from Redis/storage |

**xfail reason for storage-dependent tests**: `"Artifact processor actions require storage-proxy interaction (file download/upload/delete) which is not available in component test environment."`

### Integration Tests (`tests/integration/artifact/`)

| Test Class | Scenario | Include? |
|------------|----------|---------|
| `TestArtifactUpdateLifecycle` | DB-seed artifact → update_artifact (readonly + description) → verify updated fields | **YES** |
| `TestArtifactRevisionApprovalLifecycle` | DB-seed revision → approve_revision → verify status changed | Deferred (action may touch storage-proxy; unclear from handler code) |
| `TestArtifactRevisionRejectionLifecycle` | DB-seed revision → reject_revision → verify status changed | Deferred (same reason) |

**Primary integration test**: Only `TestArtifactUpdateLifecycle` (pure DB metadata update). Approval/rejection lifecycle tests are deferred pending verification that the approve/reject actions are purely DB state transitions with no storage-proxy side effects.

**Note**: Import/cleanup/cancel/readme/verification/progress tests are omitted from integration tests because they require external artifact registries (HuggingFace, etc.) and active storage-proxy with real file operations, which are not feasible in the standard test environment.

## Deferred Items

| Item | Reason |
|------|--------|
| `import_artifacts` full lifecycle | Requires real external artifact registry (HuggingFace) + storage-proxy download pipeline |
| `cancel_import_task` full lifecycle | Requires an active import task, which requires storage-proxy |
| `cleanup_revisions` full lifecycle | Requires stored artifact files in storage-proxy |
| `get_revision_readme` with real data | Requires stored README file in storage backend |
| `get_revision_verification_result` with real data | Requires completed verification pipeline |
| `get_revision_download_progress` with real data | Requires active/completed download progress in Redis |
| `TestArtifactRevisionApprovalLifecycle` integration | Pending verification that approve action is pure DB — not yet confirmed |
| `TestArtifactRevisionRejectionLifecycle` integration | Same as above |
| Subscription: `artifact_status_changed` | WebSocket/SSE — cannot be tested via HTTP component test client |
| Subscription: `artifact_import_progress_updated` | WebSocket/SSE — cannot be tested via HTTP component test client |

## Implementation Steps

1. Create `tests/component/artifact/__init__.py`
2. Create `tests/component/artifact/conftest.py`
   - `server_subapp_pkgs` → `[".auth", ".artifact"]`
   - `server_cleanup_contexts` → standard 8 contexts + `_artifact_domain_ctx`
   - `_artifact_domain_ctx` → Repositories + Processors initialization (same pattern as ACL)
   - Static imports: `_auth_api`, `_artifact_api`
   - `artifact_factory` fixture → creates ArtifactRegistryRow + ArtifactRow + ArtifactRevisionRow in DB
3. Create `tests/component/artifact/test_artifact.py`
   - Component tests using `admin_registry.artifact.*` methods
   - xfail-marked storage-dependent tests
4. Create `tests/component/artifact/BUILD` → `python_tests()`
5. Create `tests/integration/artifact/__init__.py`
6. Create `tests/integration/artifact/conftest.py`
   - `artifact_factory` fixture for DB seeding
7. Create `tests/integration/artifact/test_artifact.py`
   - Integration lifecycle tests for DB-only operations
8. Create `tests/integration/artifact/BUILD` → `python_tests()`
9. Run `pants fmt ::` and `pants fix ::` and `pants lint --changed-since=HEAD~1`
10. Create PR + changelog
