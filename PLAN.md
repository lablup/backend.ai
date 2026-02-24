# Implementation Plan: BA-4578

## SDK v2 Client Analysis

Source: `src/ai/backend/client/v2/domains/storage.py` — `StorageClient`

### Object Storage Methods

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `list_object_storages()` | GET | `/object-storages/` | none | Simple listing |
| `get_presigned_upload_url(req)` | POST | `/object-storages/presigned/upload` | JSON body | Needs artifact_revision_id, key |
| `get_presigned_download_url(req)` | POST | `/object-storages/presigned/download` | JSON body | Needs artifact_revision_id, key, expiration |
| `get_all_buckets()` | GET | `/object-storages/buckets` | none | Deprecated — use storage-namespaces |
| `get_buckets(storage_id)` | GET | `/object-storages/{storage_id}/buckets` | path param | Deprecated — use storage-namespaces |

### VFS Storage Methods

| Method | HTTP | Endpoint | Params style | Notes |
|--------|------|----------|-------------|-------|
| `list_vfs_storages()` | GET | `/vfs-storages/` | none | Simple listing |
| `get_vfs_storage(storage_name)` | GET | `/vfs-storages/{storage_name}` | path param | |
| `list_vfs_files(storage_name, req)` | GET | `/vfs-storages/{storage_name}/files` | path + JSON body | GET with body; server uses BodyParam — reads request.json() correctly |

## Server Handler Status

### Object Storage
- Handler file: EXISTS at `src/ai/backend/manager/api/object_storage.py` (single-file module)
- Registered in `global_subapp_pkgs`: YES (`.object_storage`)
- Routes: `POST /presigned/upload`, `POST /presigned/download`, `GET /buckets`, `GET /{storage_id}/buckets`, `GET /`
- Server endpoint not in SDK: none (all routes covered)
- Action required: **test-only**

### VFS Storage
- Handler file: EXISTS at `src/ai/backend/manager/api/vfs_storage.py` (single-file module)
- Registered in `global_subapp_pkgs`: YES (`.vfs_storage`)
- Routes: `POST /{storage_name}/download`, `GET /{storage_name}/files`, `GET /{storage_name}`, `GET /`
- Server endpoint not in SDK: `POST /{storage_name}/download` (streaming download, no SDK method)
- Action required: **test-only**

## Test Scenarios

### Component Tests (`tests/component/storage/`)

conftest.py will load subapps: `[".auth", ".object_storage", ".vfs_storage"]`

#### Object Storage

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestListObjectStorages` | `test_admin_lists_object_storages` | Admin calls GET /object-storages/ → 200 with list (possibly empty) | - |
| `TestListObjectStorages` | `test_user_lists_object_storages` | Regular user calls GET /object-storages/ → 200 | - |
| `TestGetPresignedUploadURL` | `test_presigned_upload_url_with_invalid_revision` | POST /object-storages/presigned/upload with non-existent revision_id → error | - |
| `TestGetPresignedDownloadURL` | `test_presigned_download_url_with_invalid_revision` | POST /object-storages/presigned/download with non-existent revision_id → error | - |
| `TestGetAllBuckets` | `test_admin_gets_all_buckets` | Admin calls GET /object-storages/buckets → 200 (empty if no storage configured) | - |
| `TestGetBuckets` | `test_get_buckets_with_nonexistent_storage` | GET /object-storages/{random_uuid}/buckets → error (no such storage) | - |

#### VFS Storage

| Test Class | Test Method | Scenario | xfail? |
|------------|-------------|----------|--------|
| `TestListVFSStorages` | `test_admin_lists_vfs_storages` | Admin calls GET /vfs-storages/ → 200 with list | - |
| `TestListVFSStorages` | `test_user_lists_vfs_storages` | Regular user calls GET /vfs-storages/ → 200 | - |
| `TestGetVFSStorage` | `test_get_vfs_storage_not_found` | GET /vfs-storages/nonexistent → error | - |
| `TestListVFSFiles` | `test_list_vfs_files_not_found` | GET /vfs-storages/nonexistent/files with body → error (storage not found) | xfail: GET+body — SDK sends JSON body on GET, server reads via BodyParam (works), but storage proxy unavailable in component test |

### Integration Tests (`tests/integration/storage/`)

| Test Class | Scenario |
|------------|----------|
| `TestObjectStorageLifecycle` | list_object_storages → verify response structure |
| `TestVFSStorageLifecycle` | list_vfs_storages → get_vfs_storage (if any) → verify response structure |

Note: Integration tests require real storage infrastructure. The test scope will be limited to what's available in the CI environment.

## Deferred Items

| Item | Reason |
|------|--------|
| `POST /{storage_name}/download` (VFS file download) | Streaming endpoint (`@stream_api_handler`); no SDK method; cannot be tested via standard HTTP component test client |
| Presigned URL happy-path tests | Requires real S3-compatible object storage + artifact revisions in DB; out of scope for initial component tests |
| `list_vfs_files` happy-path test | Requires live storage proxy connection; component test env has empty proxy config |

## Implementation Steps

1. Create `tests/component/storage/__init__.py`
2. Create `tests/component/storage/conftest.py` — override `server_subapp_pkgs` (`.auth`, `.object_storage`, `.vfs_storage`), `server_cleanup_contexts`, and `_storage_domain_ctx`
3. Create `tests/component/storage/test_storage.py` — component test cases per table above
4. Create `tests/component/storage/BUILD`
5. Create `tests/integration/storage/__init__.py`
6. Create `tests/integration/storage/conftest.py`
7. Create `tests/integration/storage/test_storage.py` — integration test cases per table above
8. Create `tests/integration/storage/BUILD`
9. `pants fmt :: && pants fix :: && pants lint --changed-since=HEAD~1`
10. PR + changelog
