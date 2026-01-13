---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Implemented
Created: 2026-01-06
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version: 26.1.0
---

# Pydantic Field Metadata Annotation

## Related Issues

- JIRA: BA-3766 (related)

## Motivation

Current Pydantic configuration classes have issues with field metadata management:

1. **No version information**: Cannot track when fields were added/deprecated
2. **Scattered documentation**: `Field(description=...)` and other metadata are separated
3. **No environment-specific examples**: Cannot provide different example values for local/prod environments

### Goals

- `Field` handles **validation** only
- `BackendAIFieldMeta` handles **documentation + version management**
- `Annotated` unifies all metadata in one place

## Current Design

```python
class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(
        default="local",
        description="Namespace prefix for etcd keys.",
        examples=["local", "backend"],
    )
```

### Problems

1. Cannot add version information
2. Cannot distinguish environment-specific examples
3. No way to mark deprecated fields
4. No metadata for secret value masking

## Proposed Design

### Metadata Class Structure

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigExample:
    """Environment-specific configuration examples"""
    local: str
    prod: str

@dataclass(frozen=True)
class BackendAIFieldMeta:
    """Common field metadata (documentation + version management)"""
    description: str
    added_version: str  # Required
    deprecated_version: str | None = None
    deprecation_hint: str | None = None

@dataclass(frozen=True)
class BackendAIConfigMeta(BackendAIFieldMeta):
    """Configuration field metadata"""
    example: ConfigExample | str | None = None
    secret: bool = False
    composite: bool = False  # If True, auto-generate example from child fields

@dataclass(frozen=True)
class BackendAIAPIMeta(BackendAIFieldMeta):
    """API field metadata (Request/Response)"""
    example: str | None = None
    composite: bool = False  # If True, auto-generate example from child fields
```

### Field Definition Pattern

Specify both `Field` and `Meta` in `Annotated`:

```python
from typing import Annotated
from pydantic import Field

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

    password: Annotated[
        str | None,
        Field(default=None),
        BackendAIConfigMeta(
            description="Password for etcd authentication.",
            added_version="25.1.0",
            secret=True,
        ),
    ]
```

### Composite Type Example Handling

Composite types with child fields use `composite=True` to auto-generate examples from child fields:

```python
class SessionConfig:
    cpu: Annotated[int, BackendAIAPIMeta(
        description="CPU cores.",
        added_version="25.1.0",
        example="4",
    )]
    memory: Annotated[str, BackendAIAPIMeta(
        description="Memory size.",
        added_version="25.1.0",
        example="8g",
    )]

class CreateSessionRequest:
    # Primitive type - specify example directly
    name: Annotated[str, BackendAIAPIMeta(
        description="Session name.",
        added_version="25.1.0",
        example="my-session",
    )]

    # Composite type - auto-generate example from child fields
    config: Annotated[SessionConfig, BackendAIAPIMeta(
        description="Session configuration.",
        added_version="25.1.0",
        composite=True,
    )]
```

### Metadata Retrieval and Example Generation Utilities

```python
from typing import Annotated, get_args, get_origin

def get_field_meta(
    model: type[BaseModel],
    field_name: str,
) -> BackendAIFieldMeta | None:
    """Retrieve BackendAI metadata for a field"""
    field_type = model.model_fields[field_name].annotation
    if get_origin(field_type) is Annotated:
        for arg in get_args(field_type):
            if isinstance(arg, BackendAIFieldMeta):
                return arg
    return None

def get_field_type(model: type[BaseModel], field_name: str) -> type:
    """Get the actual type of a field (unwrap Annotated)"""
    field_type = model.model_fields[field_name].annotation
    if get_origin(field_type) is Annotated:
        return get_args(field_type)[0]
    return field_type

def generate_example(model: type[BaseModel], field_name: str) -> str | dict:
    """Generate example for a field"""
    meta = get_field_meta(model, field_name)

    if not isinstance(meta, BackendAIAPIMeta):
        return ""

    # If composite=False, use direct example
    if not meta.composite:
        return meta.example or ""

    # If composite=True, combine from child fields
    field_type = get_field_type(model, field_name)
    return generate_composite_example(field_type)

def generate_composite_example(model: type[BaseModel]) -> dict:
    """Recursively generate example for composite types from child fields"""
    result = {}

    for name in model.model_fields:
        meta = get_field_meta(model, name)

        if not isinstance(meta, BackendAIAPIMeta):
            continue

        if meta.composite:
            # Recursively process child fields
            child_type = get_field_type(model, name)
            result[name] = generate_composite_example(child_type)
        else:
            result[name] = meta.example

    return result

def generate_model_example(model: type[BaseModel]) -> dict:
    """Generate example for entire model"""
    result = {}

    for name in model.model_fields:
        result[name] = generate_example(model, name)

    return result
```

**Generated Example Result:**

```python
# generate_model_example(CreateSessionRequest) result:
{
    "name": "my-session",
    "config": {
        "cpu": "4",
        "memory": "8g"
    }
}
```

## Field Summary

### BackendAIFieldMeta (Common)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `str` | ✓ | Field description |
| `added_version` | `str` | ✓ | Version when added |
| `deprecated_version` | `str \| None` | - | Version when deprecated |
| `deprecation_hint` | `str \| None` | - | Migration guidance |

### BackendAIConfigMeta (Configuration)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `example` | `ConfigExample \| str \| None` | - | Environment-specific examples |
| `secret` | `bool` | - | Whether value is secret (default: False) |
| `composite` | `bool` | - | Generate example from child fields (default: False) |

### BackendAIAPIMeta (API)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `example` | `str \| None` | - | API documentation example (string) |
| `composite` | `bool` | - | Generate example from child fields (default: False) |

## Implementation Plan

### Phase 1: Define Metadata Classes

**Goal**: Add metadata classes to common module

**Tasks**:
- Create `src/ai/backend/common/config/meta.py`
- Define `BackendAIFieldMeta`, `BackendAIConfigMeta`, `BackendAIAPIMeta` classes
- Define `ConfigExample` dataclass
- Add metadata retrieval utility functions
- Add `composite`-based example generation functions

### Phase 2: Apply to Config Classes

**Goal**: Apply `BackendAIConfigMeta` to configuration classes

**Target Files**:
- `src/ai/backend/manager/config/unified.py`
- `src/ai/backend/agent/config/unified.py`
- `src/ai/backend/storage/config/unified.py`
- `src/ai/backend/web/config/unified.py`
- `src/ai/backend/common/configs/*.py`

**Example**:
```python
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
```

### Phase 3: Apply to API Request/Response

**Goal**: Apply `BackendAIAPIMeta` to REST API DTOs

**Target Files**:
- `src/ai/backend/manager/api/*/types.py`
- `src/ai/backend/manager/dto/*.py`

**Example**:
```python
class CreateSessionRequest(BaseModel):
    name: Annotated[
        str,
        Field(min_length=1, max_length=64),
        BackendAIAPIMeta(
            description="Session name.",
            added_version="25.1.0",
            example="my-session",
        ),
    ]

    config: Annotated[
        SessionConfig,
        Field(),
        BackendAIAPIMeta(
            description="Session configuration.",
            added_version="25.1.0",
            composite=True,
        ),
    ]
```

### Phase 4: Apply to Strawberry GraphQL

**Goal**: Apply `BackendAIAPIMeta` to GraphQL schema

**Target Files**:
- `src/ai/backend/manager/api/gql/*.py`
- `src/ai/backend/manager/models/gql_models/*.py`

**Example**:
```python
@strawberry.input
class CreateSessionInput:
    name: Annotated[
        str,
        BackendAIAPIMeta(
            description="Session name.",
            added_version="25.1.0",
            example="my-session",
        ),
    ]

@strawberry.type
class SessionNode:
    id: Annotated[
        str,
        BackendAIAPIMeta(
            description="Session unique identifier.",
            added_version="25.1.0",
            example="sess-12345",
        ),
    ]
```

**Additional Tasks**:
- Custom extension to read description from Meta instead of `@strawberry.field(description=...)`
- Auto-reflect description and deprecation info from `BackendAIAPIMeta` during GraphQL schema generation

### Phase 5: CLI/Documentation Integration

**Goal**: Metadata-based automation

**Tasks**:
- Display `BackendAIConfigMeta.description` and `example` in CLI `--help`
- Mask `secret=True` fields in logs/output
- Emit runtime warning when `deprecated_version` is set
- Generate examples based on `composite` pattern for API documentation

## References

- [Pydantic Annotated Pattern](https://docs.pydantic.dev/latest/concepts/fields/#using-annotated)
- [Python typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
- [Strawberry GraphQL](https://strawberry.rocks/)
