# 아티팩트 import 대상 vfolder 지원

## 동기

현재 사용자가 `import_artifacts` API 로 아티팩트를 가져오면 내려받을 위치가 시스템 설정에 미리 구성한 `artifact_storage` 로 정해진다. 사용자가 가져온 모델의 저장 위치를 고를 수 없어 유연성이 떨어진다.

### 현재 구조

현재 아티팩트 import 흐름은 다음과 같다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client (WebUI)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ import_artifacts(artifactRevisionIds)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 Manager                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ArtifactRevisionService.import_revision()                            │  │
│  │    1. Load artifact & revision data from DB                           │  │
│  │    2. Read reservoir_config from settings                             │  │
│  │    3. Resolve storage_host from artifact_storage config               │  │
│  │    4. Build storage_step_mappings (DOWNLOAD, VERIFY, ARCHIVE)         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ POST /import (with storage_step_mappings)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Storage Proxy                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Import Pipeline                                                      │  │
│  │    1. DOWNLOAD: Fetch model from external registry (HuggingFace/etc)  │  │
│  │    2. VERIFY: Run verification (malware scan, etc.)                   │  │
│  │    3. ARCHIVE: Store to final destination                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  StoragePool                                                          │  │
│  │    ├── VFSStorage (pre-configured from config file)                   │  │
│  │    └── ObjectStorage (pre-configured from config file)                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         artifact_storage (destination)                      │
│                                                                             │
│   Pre-configured in storage-proxy.toml:                                     │
│   ┌─────────────────────┐    or    ┌─────────────────────┐                  │
│   │  VFS Storage        │          │  Object Storage     │                  │
│   │  /path/to/artifacts │          │  s3://bucket/...    │                  │
│   └─────────────────────┘          └─────────────────────┘                  │
│                                                                             │
│   ⚠️  Cannot download directly to user's VFolder                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**한계**: 모델을 사용자의 vfolder 로 바로 내려받을 수 없어 Backend.AI 의 compute 세션과 model serving 기능에 직접 연동하기 어렵다.

### 사용 사례: 모델 스토어 연동

모델 스토어 화면에서 사용자는 모델을 자신의 vfolder 로 바로 내려받을 수 있어야 한다.

1. 사용자가 모델 스토어 화면에서 "Import Model to My VFolder" 버튼을 누른다.
2. vfolder 선택 화면이 나오고, 사용자는 모델 유형 vfolder 를 생성하거나 기존 vfolder 를 고른다.
3. 고른 vfolder ID 가 `import_artifacts` mutation 에 전달되고, 모델은 미리 구성한 storage 대신 그 vfolder 로 내려받는다.

이 개선으로 사용자는 다음 위치로 모델을 내려받을 수 있다.
- 자신의 VFS(Virtual File System)
- object storage
- 모델 스토어

## 제안 변경

### API 변경

`import_artifacts` API 에 선택적 `vfolderId` parameter 를 추가한다.

### 구조 변경

#### 1. VolumeStorageAdapter 클래스

vfolder 대상을 지원하려면 `AbstractVolume`(volume backend 인터페이스)을 아티팩트 storage 대상으로 사용하는 방법이 필요하다. 기존 import pipeline 은 `AbstractStorage` 인터페이스를 기대하므로, 두 인터페이스를 잇는 `VolumeStorageAdapter` 를 도입한다.

```python
class VolumeStorageAdapter(AbstractStorage):
    """
    Adapter that wraps AbstractVolume to implement AbstractStorage interface.

    This enables using any volume backend (VFS, XFS, NetApp, GPFS, Weka, VAST, CephFS, etc.)
    as an artifact storage target without registering to StoragePool.
    """

    def __init__(
        self,
        name: str,
        volume: AbstractVolume,
        vfid: VFolderID,
    ) -> None:
        self._name = name
        self._volume = volume
        self._vfid = vfid

    async def stream_upload(self, filepath: str, data_stream: StreamReader) -> None:
        # Delegates to volume.add_file()
        ...

    async def stream_download(self, filepath: str) -> StreamReader:
        # Delegates to volume.read_file()
        ...

    async def delete_file(self, filepath: str) -> None:
        # Delegates to volume.delete_files()
        ...

    async def get_file_info(self, filepath: str) -> VFSFileMetaResponse:
        # Uses volume.sanitize_vfpath() + aiofiles.os.stat()
        ...
```

**VolumeStorageAdapter 의 주요 장점:**
- volume 의 고유 file 동작(add_file, read_file, delete_files, mkdir)을 사용한다
- 모든 vfolder backend(VFS, XFS, NetApp, GPFS, Weka, VAST, CephFS 등)를 같은 방식으로 지원한다
- StoragePool 에 등록하는 부담이 없다
- backend 별 quota 관리와 함께 동작한다
- 모든 동작을 volume 에 위임해 backend 별 최적화를 살린다

#### 2. StorageTarget 클래스

`VolumeStorageAdapter` 로 volume 을 아티팩트 storage 로 사용할 수 있게 됐다. 그러나 기존 import pipeline 은 storage 이름(string)으로 `StoragePool` 에서 storage 를 찾는다. 다음 두 가지 중 하나를 전달할 방법이 필요하다.
- 미리 구성한 storage 의 이름(`str`) - 기존 동작
- vfolder 대상에 사용하는 `VolumeStorageAdapter` 인스턴스 - 새 동작

`StorageTarget` 클래스가 이 통합 인터페이스를 제공한다.

```python
class StorageTarget:
    """
    Wrapper for storage step mapping that can be either a storage name (str)
    or a storage instance (AbstractStorage).

    When str: resolved via storage_pool.get_storage(name)
    When AbstractStorage: used directly (e.g., VolumeStorageAdapter for VFolder imports)
    """

    _value: str | AbstractStorage

    def __init__(self, value: str | AbstractStorage) -> None:
        self._value = value

    def resolve(self, storage_pool: AbstractStoragePool) -> AbstractStorage:
        """Resolve this mapping to an AbstractStorage instance."""
        if isinstance(self._value, AbstractStorage):
            return self._value
        return storage_pool.get_storage(self._value)
```

#### 3. 변경된 import step context

`ImportStepContext` 는 문자열만 사용하는 mapping 대신 `StorageTarget` 을 사용하도록 변경한다.

```python
@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: AbstractStoragePool
    storage_step_mappings: dict[ArtifactStorageImportStep, StorageTarget]
    step_metadata: dict[str, Any]
```

import step 은 이제 `StorageTarget.resolve()` 로 storage 인스턴스를 가져온다.

```python
# In import step
storage = context.storage_step_mappings[self.step_type].resolve(context.storage_pool)
await storage.stream_upload(filepath, data_stream)
```

### 요청 흐름

```
API Request with vfolderId
    │
    ▼
Parse vfid from request body
    │
    ▼
Get volume from VolumePool by volume_name
    │
    ▼
Create VolumeStorageAdapter (name: vfolder_storage_{request_id})
    │
    ▼
Create StorageTarget wrapping VolumeStorageAdapter
    │
    ▼
Build storage_step_mappings with StorageTarget instances
    │
    ▼
Start background import task ──► Return response to client
    │
    ▼
[Background task runs...]
    │
    │  Each step resolves storage via:
    │  storage = mapping.resolve(storage_pool)
    │  → Returns VolumeStorageAdapter directly
    │
    ▼
Task completes (success or failure)
```

adapter 이름에 `request_id` 를 포함해 유일성과 추적성을 보장한다.
