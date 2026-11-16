# UnifiedConfig 통합과 loader/CLI 체계

## 관련 이슈

- JIRA: BA-3766
- 관련 BEP: [BEP-1022 Pydantic field 메타데이터 어노테이션](BEP-1022-pydantic-field-annotations.md)

## 동기

### 1. 설정 class 중복

설정 class 가 여러 컴포넌트에 중복으로 존재한다.

| 설정 class | 중복 위치 | 개수 |
|--------------|---------------------|-------|
| EtcdConfig | Manager, Agent, Storage, Web, AppProxy/Coordinator | 5 |
| OTELConfig | Manager, Agent, Storage, Web, AppProxy/Worker, AppProxy/Coordinator | 6 |
| ServiceDiscoveryConfig | Manager, Agent, Storage, AppProxy/Worker, AppProxy/Coordinator | 5 |
| PyroscopeConfig | Manager, Agent, Storage, AppProxy/Common | 4 |

### 2. loader 체계는 Manager 에만 있다

현재 loader 체계는 `src/ai/backend/manager/config/loader/` 에만 있다.
- `AbstractConfigLoader` - 추상 인터페이스
- `EtcdCommonConfigLoader`, `EtcdManagerConfigLoader` - etcd 에서 값을 읽는다
- `TomlLoader` - TOML 파일에서 값을 읽는다
- `EnvLoader` - 환경 변수에서 값을 읽는다
- `LoaderChain` - 여러 loader 를 연결한다

Agent, Storage 같은 다른 컴포넌트는 이 체계를 사용할 수 없다.

### 3. 설정 관리를 위한 CLI 가 없다

설정 관리를 위한 CLI 가 없다.
- 현재 설정 값을 조회할 수 없다
- 설정 이전 도구가 없다
- field 단위 변경 기능이 없다

## 현재 설계

### 설정 class (중복)

```python
# src/ai/backend/manager/config/unified.py
class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(default="local", ...)
    addr: HostPortPair | list[HostPortPair] = Field(...)

# src/ai/backend/agent/config/unified.py (same code repeated)
class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(default="local", ...)
    addr: HostPortPair | list[HostPortPair] = Field(...)
```

### loader (Manager 전용)

```python
# src/ai/backend/manager/config/loader/types.py
class AbstractConfigLoader(ABC):
    @abstractmethod
    async def load(self) -> Mapping[str, Any]:
        raise NotImplementedError

# src/ai/backend/manager/config/loader/etcd_loader.py
class EtcdCommonConfigLoader(AbstractConfigLoader):
    async def load(self) -> Mapping[str, Any]:
        return await self._etcd.get_prefix("ai/backend/config/common")
```

## 제안 설계

### 1. 설정 class 통합

`src/ai/backend/common/configs/` 로 통합하고 BEP-1022 메타데이터를 적용한다.

```python
# src/ai/backend/common/configs/etcd.py
from typing import Annotated
from pydantic import Field
from ai.backend.common.config.meta import BackendAIConfigMeta, ConfigExample

class EtcdConfig(BaseConfigSchema):
    namespace: Annotated[
        str,
        Field(default="local"),
        BackendAIConfigMeta(
            description="Namespace prefix for etcd keys.",
            added_version="25.1.0",
            example=ConfigExample(local="local", prod="backend"),
        ),
    ]

    addr: Annotated[
        HostPortPair | list[HostPortPair],
        Field(default_factory=lambda: HostPortPair(host="127.0.0.1", port=2379)),
        BackendAIConfigMeta(
            description="etcd server address.",
            added_version="25.1.0",
            example=ConfigExample(
                local="127.0.0.1:2379",
                prod="etcd.cluster.internal:2379",
            ),
        ),
    ]

    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Password for etcd authentication.",
            added_version="25.1.0",
            secret=True,
            # example omitted - secret value
        ),
    ]
```

**복합 타입 설정:**

자식 field 를 가진 설정은 BEP-1022 의 `composite` 패턴을 사용한다.

```python
class DatabaseConfig(BaseConfigSchema):
    host: Annotated[
        str,
        Field(default="localhost"),
        BackendAIConfigMeta(
            description="Database host.",
            added_version="25.1.0",
            example=ConfigExample(local="localhost", prod="db.internal"),
        ),
    ]
    port: Annotated[
        int,
        Field(default=5432),
        BackendAIConfigMeta(
            description="Database port.",
            added_version="25.1.0",
            example="5432",
        ),
    ]

class ManagerConfig(BaseConfigSchema):
    # Composite type - auto-generate example from child fields
    database: Annotated[
        DatabaseConfig,
        Field(default_factory=DatabaseConfig),
        BackendAIConfigMeta(
            description="Database configuration.",
            added_version="25.1.0",
            composite=True,  # Combine example from child fields
        ),
    ]
```

### 2. 공용 loader 체계

```
src/ai/backend/common/config/
├── loader/
│   ├── __init__.py
│   ├── types.py              # AbstractConfigLoader
│   ├── etcd_loader.py        # EtcdConfigLoader
│   ├── toml_loader.py        # TomlConfigLoader
│   ├── env_loader.py         # EnvConfigLoader
│   └── loader_chain.py       # LoaderChain
└── meta.py                   # BEP-1022 metadata
```

```python
# src/ai/backend/common/config/loader/types.py
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

class AbstractConfigLoader(ABC):
    """Abstract interface for configuration loaders"""

    @abstractmethod
    async def load(self) -> Mapping[str, Any]:
        """Load configuration values"""
        raise NotImplementedError

    @abstractmethod
    def get_source_name(self) -> str:
        """Get loader source name (for CLI display)"""
        raise NotImplementedError
```

```python
# src/ai/backend/common/config/loader/etcd_loader.py
class EtcdConfigLoader(AbstractConfigLoader):
    def __init__(self, etcd: AsyncEtcd, prefix: str) -> None:
        self._etcd = etcd
        self._prefix = prefix

    async def load(self) -> Mapping[str, Any]:
        return await self._etcd.get_prefix(self._prefix)

    def get_source_name(self) -> str:
        return f"etcd:{self._prefix}"
```

### 3. CLI 체계

```
./backend.ai config <subcommand>
```

| 하위 명령 | 설명 |
|------------|-------------|
| `show` | 현재 설정 값을 표시한다 |
| `show --source` | 각 값의 loader 출처를 표시한다 |
| `get <key>` | 특정 key 의 값을 조회한다 |
| `set <key> <value>` | 특정 key 의 값을 변경한다 |
| `migrate` | legacy 설정을 새 형식으로 이전한다 |
| `validate` | 설정을 검증한다 |
| `export` | 설정을 파일로 내보낸다 |

#### CLI 예시

```bash
# Display current configuration
$ ./backend.ai mgr config show
etcd:
  namespace: backend
  addr: etcd.cluster.internal:2379
  password: ********  # secret fields are masked

# Display with source information
$ ./backend.ai mgr config show --source
etcd:
  namespace: backend          [etcd:ai/backend/config/common]
  addr: etcd.cluster.internal:2379  [toml:manager.toml]
  password: ********          [env:BACKEND_ETCD_PASSWORD]

# Get specific value
$ ./backend.ai mgr config get etcd.namespace
backend

# Set value
$ ./backend.ai mgr config set etcd.namespace production

# Migration
$ ./backend.ai mgr config migrate --from-legacy
Migrating legacy config...
  [OK] etcd.namespace: local -> backend
  [OK] etcd.addr: 127.0.0.1:2379 -> etcd.cluster.internal:2379
Migration complete.
```

### 4. 설정 출처 추적

각 설정 값을 어느 loader 에서 읽었는지 추적한다.

```python
@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    value: Any
    source: str  # "etcd:...", "toml:...", "env:..."
    meta: BackendAIConfigMeta | None

class ConfigRegistry:
    """Configuration registry (source tracking)"""
    _values: dict[str, ConfigValue]

    def get(self, key: str) -> ConfigValue:
        return self._values[key]

    def get_by_source(self, source: str) -> dict[str, ConfigValue]:
        return {k: v for k, v in self._values.items() if v.source.startswith(source)}
```

## 구현 계획

### 1단계: 메타데이터 class (BEP-1022)

- `BackendAIFieldMeta`, `BackendAIConfigMeta` class 를 구현한다
- `ConfigExample` dataclass 를 구현한다
- 메타데이터 조회 유틸리티를 구현한다

### 2단계: 설정 class 통합

**생성할 파일 (4개)**:
- `src/ai/backend/common/configs/etcd.py`
- `src/ai/backend/common/configs/otel.py`
- `src/ai/backend/common/configs/service_discovery.py`
- `src/ai/backend/common/configs/pyroscope.py`

**수정할 파일 (8개)**:
- `src/ai/backend/manager/config/unified.py`
- `src/ai/backend/agent/config/unified.py`
- `src/ai/backend/storage/config/unified.py`
- `src/ai/backend/web/config/unified.py`
- `src/ai/backend/appproxy/coordinator/config.py`
- `src/ai/backend/appproxy/worker/config.py`
- `src/ai/backend/appproxy/common/config.py`
- `src/ai/backend/common/configs/__init__.py`

### 3단계: 공용 loader 체계

**생성할 파일**:
- `src/ai/backend/common/config/loader/types.py`
- `src/ai/backend/common/config/loader/etcd_loader.py`
- `src/ai/backend/common/config/loader/toml_loader.py`
- `src/ai/backend/common/config/loader/env_loader.py`
- `src/ai/backend/common/config/loader/loader_chain.py`

**이전**:
- 기존 loader 를 Manager 에서 common 으로 이전한다
- 각 컴포넌트가 공용 loader 를 사용하도록 수정한다

### 4단계: CLI 구현

**생성할 파일**:
- `src/ai/backend/common/cli/config.py` - config 하위 명령

**수정할 파일**:
- config 하위 명령을 각 컴포넌트의 CLI 에 연결한다

### 5단계: 이전 도구

- legacy 설정 형식을 감지한다
- 자동 이전 script
- 이전 검증

## 범위 밖

- **AccountManager**: 기반 class 와 요구 사항이 다르다
- **DebugConfig**: 컴포넌트별 field 차이가 너무 크다

## 참고

- [BEP-1022: Pydantic field 메타데이터 어노테이션](BEP-1022-pydantic-field-annotations.md)
- [기존 Manager loader](../src/ai/backend/manager/config/loader/)
- [기존 공용 설정](../src/ai/backend/common/configs/)
