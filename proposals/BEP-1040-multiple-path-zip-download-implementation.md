---
Author: TaekYoung Kwon (tykwon@lablup.com)
Status: Draft
Created: 2025-01-27
Created-Version: 26.2.0
Target-Version:
Implemented-Version:
---

# BEP-1040: Multiple Path ZIP Download Implementation

## Related Issues

- GitHub: [#7765](https://github.com/lablup/backend.ai/issues/7765)
- JIRA: [BA-3743](https://lablup.atlassian.net/browse/BA-3743)
- JIRA: [BA-4075](https://lablup.atlassian.net/browse/BA-4075)

## Motivation

Currently the storage proxy's download endpoint only supports single-file downloads via a JWT token
containing one `relpath`. Users who need multiple files must download them one by one.
This proposal adds multi-file ZIP download while also restructuring the streaming pipeline
for future archive format extensibility (tar, tar.gz, etc.).

## Current Design

### Download Flow

```
Client ──①─→ Manager (POST /folders/{name}/request-download)
              │ Validate permission, generate JWT
Client ←─②── Manager ({ token, url })
              │
Client ──③─→ Storage Proxy (GET /download?token=…)
              │ Verify JWT, resolve path, stream file
Client ←─④── Storage Proxy (binary stream)
```

### Current JWT Token Structure

```json
{
  "op": "download",
  "volume": "volume1",
  "vfid": "user:{user_uuid}/{folder_uuid}",
  "relpath": "data/model.bin",
  "exp": 1769486280
}
```

**Limitation**: Only supports single `relpath`. Abbreviated field names (`op`, `vfid`) reduce readability.

### Current ZIP Streaming Pipeline Analysis

`download_directory_as_archive()` in `client.py` performs three distinct phases:

**Phase 1 — File traversal and ZIP entry registration (synchronous, lightweight)**

```python
zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
for root, dirs, files in os.walk(file_path):   # sync directory traversal
    for file in files:
        zf.write(Path(root) / file, arcname=...)  # registers metadata only, no file read
```

`zf.write()` is lazy — it records "compress this file later" without reading any content.
This entire phase is metadata-only I/O and completes quickly.

**Phase 2 — Sync-to-async bridge via `_iter2aiter` + `janus.Queue`**

```
┌──────────────────┐    janus.Queue(maxsize=8)    ┌────────────────────┐
│  Thread (executor)│                              │  Async Event Loop  │
│                   │                              │                    │
│  for chunk in zf: │──── sync_q.put(chunk) ────→  │  await async_q.get()│
│    (read + compress)                             │  yield chunk       │
│  sync_q.put(SENTINEL) ── signals done ────────→  │  break             │
└──────────────────┘                               └────────────────────┘
```

When `zf` is iterated, files are actually read and compressed — this is the heavy work.
`janus.Queue` with `maxsize=8` provides backpressure between the producer thread and the async consumer.
`SENTINEL` is a marker object that signals the end of iteration, breaking the `while True` consumer loop.

**Phase 3 — HTTP streaming via `web.StreamResponse`**

```python
response = web.StreamResponse(headers={Content-Type: application/zip, ...})
await response.prepare(request)
async for chunk in _iter2aiter(zf):
    await response.write(chunk)   # stream to client
```

No `Content-Length` is set because the ZIP size is unknown until compression completes.
Uses `Transfer-Encoding: chunked` implicitly.

**Observation**: Phase 1 (traversal + registration) uses the same `_iter2aiter` bridge
as Phase 2 (compression + streaming), but Phase 1 doesn't need it — it's lightweight enough
for `asyncio.to_thread`. The generic `_iter2aiter` helper obscures these different requirements.

## Proposed Design

### 1. New JWT Token for Multi-File Download

```json
{
  "operation": "download",
  "volume": "volume1",
  "vfolder_id": "user:{user_uuid}/{folder_uuid}",
  "files": ["data/model.bin", "data/config.json", "logs/"],
  "exp": 1769486280
}
```

**Decision**: Use separate token structure with new field names instead of extending the existing one.

**Rationale**: Adding `files` to the existing token could affect the legacy `download()` handler.
New field names (`operation` instead of `op`, `vfolder_id` instead of `vfid`) improve readability
and clearly distinguish the two token types.

### 2. Pydantic Token Validation

```python
class ArchiveDownloadTokenData(BaseModel):
    operation: Literal["download"]
    volume: str
    vfolder_id: VFolderID
    files: list[str] = Field(min_length=1)
```

**Decision**: Use pydantic instead of trafaret `tx.JsonWebToken`.

**Rationale**: New code reduces trafaret dependency. Pydantic provides built-in validation
(e.g., `min_length=1`) and clear error messages via `ValidationError`.

### 3. Pre-validation Strategy

All file paths are validated **before** ZIP streaming begins:

```python
for relpath_str in token_data.files:
    file_path = (vfpath / relpath_str).resolve()
    file_path.relative_to(vfpath.resolve())   # path traversal check
    if not file_path.exists():                 # existence check
        raise HTTPNotFound(...)
```

**Decision**: Halt on first error (fail-fast).

**Rationale**:

| | Halt (adopted) | Continue (rejected) |
|---|---|---|
| Behavior | 404 if any file missing | ZIP with available files + `X-Missing-Files` header |
| Data integrity | Guaranteed — all-or-nothing | User may not notice missing files |
| Complexity | Simple — one validation loop | Requires collecting errors, partial ZIP, extra headers |

Pre-validation is possible because `zf.write()` is lazy. The entire registration phase runs
before any file is actually read, so we can check all paths and abort with a clean HTTP error
before the streaming response begins.

### 4. Streaming Pipeline — `StreamReader` ABC

**Decision**: Implement the ZIP streaming as a `StreamReader` subclass instead of standalone functions.

**Rationale**: `StreamReader` (defined in `ai.backend.common.types`) is the existing ABC for
byte-stream producers across the codebase. 10+ implementations already exist (S3, HuggingFace,
VFS file, VFS directory/tar, CSV export, etc.). All follow a flat hierarchy — no intermediate
ABCs are needed.

Using `StreamReader` enables:
- The consumer (HTTP response writer) to be format-agnostic
- Future archive formats (tar, tar.gz) to be added as new `StreamReader` implementations
- Consistency with the existing streaming patterns in the project

**`ZipArchiveStreamReader` implementation sketch:**

```python
class ZipArchiveStreamReader(StreamReader):
    def __init__(self, base_path: Path, entries: list[tuple[str, Path]]) -> None:
        self._zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
        for arcname, file_path in entries:
            if file_path.is_file():
                self._zf.write(file_path, arcname=arcname)
            elif file_path.is_dir():
                for root, dirs, files in os.walk(file_path):
                    root_path = Path(root)
                    for f in files:
                        self._zf.write(root_path / f, Path(arcname) / root_path.relative_to(file_path) / f)
                    if not dirs and not files:
                        self._zf.write(root, Path(arcname) / root_path.relative_to(file_path))

    def content_type(self) -> str:
        return "application/zip"

    async def read(self) -> AsyncIterator[bytes]:
        q: janus.Queue[bytes | Sentinel] = janus.Queue(maxsize=DEFAULT_INFLIGHT_CHUNKS)
        try:
            fut = asyncio.get_running_loop().run_in_executor(None, self._feed, q.sync_q)
            while True:
                item = await q.async_q.get()
                if isinstance(item, Sentinel):
                    break
                yield item
            await fut
        finally:
            q.close()
            await q.wait_closed()

    def _feed(self, q: janus.SyncQueue[bytes | Sentinel]) -> None:
        for chunk in self._zf:
            q.put(chunk)
        q.put(SENTINEL)
```

**Key design points:**
- `__init__`: Synchronous file traversal + `zf.write()` registration (metadata only, no file reads)
- `read()`: Async generator — actual file reads and compression happen here via `janus.Queue` bridge
- `_feed()`: Runs in thread executor, produces compressed chunks into the queue

**Consumer side** (format-agnostic):

```python
async def stream_archive_response(
    request: web.Request,
    reader: StreamReader,
    filename: str,
) -> web.StreamResponse:
    response = web.StreamResponse(headers={
        hdrs.CONTENT_TYPE: reader.content_type() or "application/octet-stream",
        hdrs.CONTENT_DISPOSITION: f'attachment; filename="{filename}"',
    })
    await response.prepare(request)
    async for chunk in reader.read():
        await response.write(chunk)
    return response
```

This function works with any `StreamReader` — ZIP, tar, or future formats.

**Why not add an intermediate `ArchiveStreamReader` ABC?**

Considered adding `StreamReader → ArchiveStreamReader → Zip/Tar/TarGz` but rejected because:
- ZIP and tar have no shared archive-building logic to extract into a base class
- `content_type()` already distinguishes formats — no additional type discrimination needed
- All 10+ existing `StreamReader` implementations use flat inheritance; adding a layer breaks consistency
- No call site needs to distinguish "archive readers" from other stream readers

### 5. Existing Implementation Compatibility

The new `ZipArchiveStreamReader` and `stream_archive_response` are **additive**.
Existing `download()`, `download_directory_as_archive()`, and `_iter2aiter()` remain untouched.

The VFS directory download in the V1 API (`VFSDirectoryDownloadServerStreamReader`)
uses tar format with a temp-file approach — a different trade-off from zipstream's in-memory streaming.
Both coexist under the `StreamReader` interface.

### 6. Stream Interruption

| Scenario | Behavior |
|----------|----------|
| Client disconnects | TCP cleanup, stream stops (HTTP standard) |
| Server-side file read error | Stream terminates (incomplete ZIP) |

ZIP streaming cannot support pause/resume because:
- No `Content-Length` (chunked transfer encoding)
- HTTP Range requests require known content length
- ZIP Central Directory is written at the end — partial ZIP is invalid

### 7. Manager-Facing Token Creation

New endpoint in storage proxy's manager-facing API:

```
POST /folder/file/download-archive
Input:  { volume, vfid, files: [...] }
Output: { token: "<jwt>" }
```

## Migration / Compatibility

### Backward Compatibility
- Existing single-file download endpoint (`GET /download`) is unchanged
- Existing JWT token structure is unchanged
- New endpoint (`GET /download-archive`) is purely additive

### Breaking Changes
None.

## Implementation Plan

### Phase 1: Storage Proxy
- [ ] Add `ArchiveDownloadTokenData` pydantic model
- [ ] Implement `ZipArchiveStreamReader` as `StreamReader` subclass
- [ ] Implement `stream_archive_response` helper
- [ ] Implement `multi_download` handler with pre-validation
- [ ] Register `GET /download-archive` route (client-facing)
- [ ] Implement `create_archive_download_session` (manager-facing)
- [ ] Register `POST /folder/file/download-archive` route (manager-facing)
- [ ] Unit tests

### Phase 2: Manager
- [ ] Add manager-side request handler for multi-file download
- [ ] Extend `CreateDownloadSessionAction` to support file list
- [ ] Add manager-facing client method for `download-archive`

### Phase 3: Client
- [ ] Update Web UI for multi-file selection
- [ ] Update client SDK

## Open Questions

- Should `__init__` of `ZipArchiveStreamReader` use `asyncio.to_thread` for large directory traversals,
  or is synchronous `os.walk` acceptable given the metadata-only nature of registration?
- Should we consider migrating the existing `download_directory_as_archive()` to use `StreamReader`
  in a follow-up, or leave it as-is?

## References

- Current implementation: `src/ai/backend/storage/api/client.py`
- `StreamReader` ABC: `src/ai/backend/common/types.py`
- Existing tar implementation: `src/ai/backend/storage/storages/vfs_storage.py` (`VFSDirectoryDownloadServerStreamReader`)
- ZIP streaming library: `zipstream-new~=1.1.8`
- JWT library: `PyJWT~=2.10.1`
