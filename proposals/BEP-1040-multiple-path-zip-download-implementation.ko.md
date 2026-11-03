# BEP-1040: 다중 경로 ZIP 다운로드 구현

## 관련 이슈

- GitHub: [#7765](https://github.com/lablup/backend.ai/issues/7765)
- JIRA: [BA-3743](https://lablup.atlassian.net/browse/BA-3743)
- JIRA: [BA-4075](https://lablup.atlassian.net/browse/BA-4075)

## 동기

지금 Storage Proxy 의 다운로드 엔드포인트는 `relpath` 하나를 담은 JWT 토큰으로 단일 파일 다운로드만 지원한다. 여러 파일이 필요한 사용자는 파일을 하나씩 내려받아야 한다. 이 제안은 다중 파일 ZIP 다운로드를 추가하고, 이후 tar, tar.gz 같은 아카이브 형식으로 확장할 수 있도록 스트리밍 파이프라인을 함께 재구성한다.

## 현재 설계

### 다운로드 흐름

```
Client ──①─→ Manager (POST /folders/{name}/request-download)
              │ Validate permission, generate JWT
Client ←─②── Manager ({ token, url })
              │
Client ──③─→ Storage Proxy (GET /download?token=…)
              │ Verify JWT, resolve path, stream file
Client ←─④── Storage Proxy (binary stream)
```

### 현재 JWT 토큰 구조

```json
{
  "op": "download",
  "volume": "volume1",
  "vfid": "user:{user_uuid}/{folder_uuid}",
  "relpath": "data/model.bin",
  "exp": 1769486280
}
```

**한계**: `relpath` 하나만 지원한다. 축약한 field 이름(`op`, `vfid`)은 가독성을 떨어뜨린다.

### 현재 ZIP 스트리밍 파이프라인 분석

`client.py` 의 `download_directory_as_archive()` 는 세 단계로 나뉜다.

**1단계: 파일 순회와 ZIP entry 등록(동기, 경량)**

```python
zf = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)
for root, dirs, files in os.walk(file_path):   # sync directory traversal
    for file in files:
        zf.write(Path(root) / file, arcname=...)  # registers metadata only, no file read
```

`zf.write()` 는 lazy 하게 동작한다. 파일 내용을 읽지 않고 "나중에 이 파일을 압축한다"는 사실만 기록한다. 이 단계 전체는 metadata 만 다루는 I/O 이고 빠르게 끝난다.

**2단계: `_iter2aiter` 와 `janus.Queue` 를 통한 동기-비동기 연결**

```
┌──────────────────┐    janus.Queue(maxsize=8)    ┌────────────────────┐
│  Thread (executor)│                              │  Async Event Loop  │
│                   │                              │                    │
│  for chunk in zf: │──── sync_q.put(chunk) ────→  │  await async_q.get()│
│    (read + compress)                             │  yield chunk       │
│  sync_q.put(SENTINEL) ── signals done ────────→  │  break             │
└──────────────────┘                               └────────────────────┘
```

`zf` 를 순회할 때 파일을 실제로 읽고 압축한다. 이 부분이 무거운 작업이다. `maxsize=8` 인 `janus.Queue` 가 producer thread 와 async consumer 사이에 backpressure 를 제공한다. `SENTINEL` 은 순회가 끝났음을 알리는 marker 객체이고, `while True` consumer loop 를 끝낸다.

**3단계: `web.StreamResponse` 를 통한 HTTP 스트리밍**

```python
response = web.StreamResponse(headers={Content-Type: application/zip, ...})
await response.prepare(request)
async for chunk in _iter2aiter(zf):
    await response.write(chunk)   # stream to client
```

압축이 끝날 때까지 ZIP 크기를 알 수 없으므로 `Content-Length` 를 설정하지 않는다. `Transfer-Encoding: chunked` 를 암묵적으로 사용한다.

**관찰**: 1단계(순회와 등록)는 2단계(압축과 스트리밍)와 같은 `_iter2aiter` 연결을 사용하지만 1단계에는 그 연결이 필요 없다. `asyncio.to_thread` 로 처리할 만큼 가볍다. 범용 `_iter2aiter` helper 가 이렇게 서로 다른 요구를 감춘다.

## 제안 설계

### 1. 다중 파일 다운로드용 새 JWT 토큰

```json
{
  "operation": "download",
  "volume": "volume1",
  "vfolder_id": "user:{user_uuid}/{folder_uuid}",
  "files": ["data/model.bin", "data/config.json", "logs/"],
  "exp": 1769486280
}
```

**결정**: 기존 토큰을 확장하지 않고 새 field 이름을 가진 별도 토큰 구조를 사용한다.

**근거**: 기존 토큰에 `files` 를 추가하면 legacy `download()` handler 에 영향을 줄 수 있다. 새 field 이름(`op` 대신 `operation`, `vfid` 대신 `vfolder_id`)은 가독성을 높이고 두 토큰 유형을 분명히 구분한다.

### 2. Pydantic 토큰 검증

```python
class ArchiveDownloadTokenData(BaseModel):
    operation: Literal["download"]
    volume: str
    vfolder_id: VFolderID
    files: list[str] = Field(min_length=1)
```

**결정**: trafaret `tx.JsonWebToken` 대신 pydantic 을 사용한다.

**근거**: 새 코드에서 trafaret 의존성을 줄인다. pydantic 은 기본 검증(`min_length=1` 등)과 `ValidationError` 를 통한 명확한 에러 메시지를 제공한다.

### 3. 사전 검증 전략

ZIP 스트리밍을 시작하기 **전에** 모든 파일 경로를 검증한다.

```python
for relpath_str in token_data.files:
    file_path = (vfpath / relpath_str).resolve()
    file_path.relative_to(vfpath.resolve())   # path traversal check
    if not file_path.exists():                 # existence check
        raise HTTPNotFound(...)
```

**결정**: 첫 에러에서 중단한다(fail-fast).

**근거**:

| | 중단(채택) | 계속(기각) |
|---|---|---|
| 동작 | 파일이 하나라도 없으면 404 | 있는 파일로 ZIP 을 생성하고 `X-Missing-Files` header 를 붙임 |
| 데이터 무결성 | 보장한다. 전부 아니면 전무 | 사용자가 빠진 파일을 알아차리지 못할 수 있다 |
| 복잡도 | 단순하다. 검증 loop 하나 | 에러 수집, 부분 ZIP, 추가 header 가 필요하다 |

사전 검증이 가능한 이유는 `zf.write()` 가 lazy 하기 때문이다. 등록 단계 전체가 실제 파일 읽기 전에 실행되므로 모든 경로를 검사하고 스트리밍 응답을 시작하기 전에 명확한 HTTP 에러로 중단할 수 있다.

### 4. 스트리밍 파이프라인: `StreamReader` ABC

**결정**: ZIP 스트리밍을 독립 함수 대신 `StreamReader` 하위 클래스로 구현한다.

**근거**: `StreamReader`(`ai.backend.common.types` 에 정의)는 코드베이스 전반에서 byte stream producer 에 사용하는 기존 ABC 다. 10개 이상 구현(S3, HuggingFace, VFS file, VFS directory/tar, CSV export 등)이 이미 있다. 모두 평평한 계층 구조를 따르므로 중간 ABC 가 필요 없다.

`StreamReader` 를 사용하면 다음이 가능하다.

- consumer(HTTP 응답 writer)가 형식과 무관해진다
- 이후 아카이브 형식(tar, tar.gz)을 새 `StreamReader` 구현으로 추가할 수 있다
- 프로젝트의 기존 스트리밍 패턴과 일관성을 유지한다

**`ZipArchiveStreamReader` 구현 개요:**

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

**핵심 설계 항목:**

- `__init__`: 동기 파일 순회와 `zf.write()` 등록(metadata 만 다루고 파일은 읽지 않는다)
- `read()`: async generator. 실제 파일 읽기와 압축은 여기서 `janus.Queue` 연결을 통해 일어난다
- `_feed()`: thread executor 에서 실행되어 압축한 chunk 를 queue 에 넣는다

**소비자 쪽(형식 독립적):**

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

이 함수는 `StreamReader` 라면 무엇이든 동작한다. ZIP, tar, 이후 형식 모두 해당한다.

**중간 `ArchiveStreamReader` ABC 를 두지 않는 이유**

`StreamReader → ArchiveStreamReader → Zip/Tar/TarGz` 계층을 추가하는 방안을 검토했지만 기각했다.

- ZIP 과 tar 는 base class 로 분리할 공통 아카이브 생성 로직이 없다
- `content_type()` 이 이미 형식을 구분하므로 추가 타입 구분이 필요 없다
- 기존 `StreamReader` 구현 10개 이상이 모두 평평한 상속을 사용하므로 계층을 추가하면 일관성이 깨진다
- "archive reader"를 다른 stream reader 와 구분해야 하는 호출 지점이 없다

### 5. 기존 구현과의 호환성

새 `ZipArchiveStreamReader` 와 `stream_archive_response` 는 **추가**다. 기존 `download()`, `download_directory_as_archive()`, `_iter2aiter()` 는 그대로 둔다.

V1 API 의 VFS directory 다운로드(`VFSDirectoryDownloadServerStreamReader`)는 임시 파일 방식으로 tar 형식을 사용한다. zipstream 의 인메모리 스트리밍과 다른 트레이드오프다. 둘 다 `StreamReader` 인터페이스 아래에 함께 존재한다.

### 6. 스트림 중단

| 시나리오 | 동작 |
|----------|----------|
| 클라이언트 연결 끊김 | TCP cleanup, 스트림 중단(HTTP 표준) |
| 서버 쪽 파일 읽기 에러 | 스트림 종료(불완전한 ZIP) |

ZIP 스트리밍은 pause/resume 를 지원할 수 없다.

- `Content-Length` 가 없다(chunked transfer encoding)
- HTTP Range 요청은 `Content-Length` 를 알아야 한다
- ZIP Central Directory 는 끝에 기록되므로 부분 ZIP 은 유효하지 않다

### 7. Manager 쪽 토큰 생성

Storage Proxy 의 manager 쪽 API 에 새 엔드포인트를 둔다.

```
POST /folder/file/download-archive
Input:  { volume, vfid, files: [...] }
Output: { token: "<jwt>" }
```

## 마이그레이션, 호환성

### 하위 호환성

- 기존 단일 파일 다운로드 엔드포인트(`GET /download`)는 변경되지 않는다
- 기존 JWT 토큰 구조는 변경되지 않는다
- 새 엔드포인트(`GET /download-archive`)는 기존 동작에 영향을 주지 않는 추가다

### 기존 호환성을 깨는 변경

없다.

## 구현 계획

### 1단계: Storage Proxy

- [ ] `ArchiveDownloadTokenData` pydantic model 추가
- [ ] `ZipArchiveStreamReader` 를 `StreamReader` 하위 클래스로 구현
- [ ] `stream_archive_response` helper 구현
- [ ] 사전 검증을 포함한 `multi_download` handler 구현
- [ ] `GET /download-archive` route 등록(client 쪽)
- [ ] `create_archive_download_session` 구현(manager 쪽)
- [ ] `POST /folder/file/download-archive` route 등록(manager 쪽)
- [ ] 단위 test

### 2단계: Manager

- [ ] 다중 파일 다운로드용 manager 쪽 요청 handler 추가
- [ ] `CreateDownloadSessionAction` 이 파일 목록을 받도록 확장
- [ ] `download-archive` 용 manager 쪽 client 메서드 추가

### 3단계: 클라이언트

- [ ] Web UI 에 다중 파일 선택 반영
- [ ] client SDK 반영

## 열린 질문

- `ZipArchiveStreamReader` 의 `__init__` 이 큰 디렉터리 순회에 `asyncio.to_thread` 를 사용하는 방안, 등록 단계가 metadata 만 다루므로 동기 `os.walk` 를 유지하는 방안
- 기존 `download_directory_as_archive()` 를 후속 작업에서 `StreamReader` 로 옮기는 방안, 그대로 두는 방안

## 참고

- 현재 구현: `src/ai/backend/storage/api/client.py`
- `StreamReader` ABC: `src/ai/backend/common/types.py`
- 기존 tar 구현: `src/ai/backend/storage/storages/vfs_storage.py` (`VFSDirectoryDownloadServerStreamReader`)
- ZIP 스트리밍 라이브러리: `zipstream-new~=1.1.8`
- JWT 라이브러리: `PyJWT~=2.10.1`
