---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-01-06
Created-Version: 26.1.0
Target-Version:
Implemented-Version:
---

# UnifiedConfig Consolidation and Loader/CLI System

## Related Issues

- JIRA: BA-3766
- Related BEP: [BEP-1022 Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)

## Motivation

### 1. Duplicated Configuration Classes

Configuration classes are duplicated across multiple components:

| Config Class | Duplicate Locations | Count |
|--------------|---------------------|-------|
| EtcdConfig | Manager, Agent, Storage, Web, AppProxy/Coordinator | 5 |
| OTELConfig | Manager, Agent, Storage, Web, AppProxy/Worker, AppProxy/Coordinator | 6 |
| ServiceDiscoveryConfig | Manager, Agent, Storage, AppProxy/Worker, AppProxy/Coordinator | 5 |
| PyroscopeConfig | Manager, Agent, Storage, AppProxy/Common | 4 |

### 2. Loader System Only Exists in Manager

Currently, the Loader system only exists in `src/ai/backend/manager/config/loader/`:
- `AbstractConfigLoader` - Abstract interface
- `EtcdCommonConfigLoader`, `EtcdManagerConfigLoader` - Load from etcd
- `TomlLoader` - Load from TOML files
- `EnvLoader` - Load from environment variables
- `LoaderChain` - Chain multiple loaders

Other components (Agent, Storage, etc.) cannot utilize this system.

### 3. No CLI for Configuration Management

No CLI exists for configuration management:
- Cannot query current configuration values
- No configuration migration tools
- No per-field update functionality

## Current Design

### Configuration Classes (Duplicated)

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

### Loader (Manager Only)

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

## Proposed Design

### 1. Consolidate Configuration Classes

Consolidate to `src/ai/backend/common/configs/` and apply BEP-1022 metadata:

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

**For Composite Type Configurations:**

Configurations with child fields use the `composite` pattern from BEP-1022:

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

### 2. Common Loader System

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

### 3. CLI System

```
./backend.ai config <subcommand>
```

| Subcommand | Description |
|------------|-------------|
| `show` | Display current configuration values |
| `show --source` | Display loader source for each value |
| `get <key>` | Get value for a specific key |
| `set <key> <value>` | Set value for a specific key |
| `migrate` | Migrate legacy config to new format |
| `validate` | Validate configuration |
| `export` | Export configuration to file |

#### CLI Examples

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

### 4. Configuration Source Tracking

Track which loader each configuration value came from:

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

## Implementation Plan

### Phase 1: Metadata Classes (BEP-1022)

- Implement `BackendAIFieldMeta`, `BackendAIConfigMeta` classes
- Implement `ConfigExample` dataclass
- Implement metadata retrieval utilities

### Phase 2: Consolidate Configuration Classes

**Files to Create (4)**:
- `src/ai/backend/common/configs/etcd.py`
- `src/ai/backend/common/configs/otel.py`
- `src/ai/backend/common/configs/service_discovery.py`
- `src/ai/backend/common/configs/pyroscope.py`

**Files to Modify (8)**:
- `src/ai/backend/manager/config/unified.py`
- `src/ai/backend/agent/config/unified.py`
- `src/ai/backend/storage/config/unified.py`
- `src/ai/backend/web/config/unified.py`
- `src/ai/backend/appproxy/coordinator/config.py`
- `src/ai/backend/appproxy/worker/config.py`
- `src/ai/backend/appproxy/common/config.py`
- `src/ai/backend/common/configs/__init__.py`

### Phase 3: Common Loader System

**Files to Create**:
- `src/ai/backend/common/config/loader/types.py`
- `src/ai/backend/common/config/loader/etcd_loader.py`
- `src/ai/backend/common/config/loader/toml_loader.py`
- `src/ai/backend/common/config/loader/env_loader.py`
- `src/ai/backend/common/config/loader/loader_chain.py`

**Migration**:
- Move existing Loaders from Manager to common
- Update each component to use common Loaders

### Phase 4: CLI Implementation

**Files to Create**:
- `src/ai/backend/common/cli/config.py` - config subcommand

**Files to Modify**:
- Connect config subcommand to each component's CLI

### Phase 5: Migration Tools

- Detect legacy configuration formats
- Automatic migration scripts
- Migration validation

## Out of Scope

- **AccountManager**: Different base class, different requirements
- **DebugConfig**: Component-specific fields vary too much

## References

- [BEP-1022: Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)
- [Existing Manager Loader](../src/ai/backend/manager/config/loader/)
- [Existing Common Configs](../src/ai/backend/common/configs/)
