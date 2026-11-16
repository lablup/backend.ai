# pydantic field metadata annotation

## 관련 이슈

- JIRA: BA-3766 (관련)

## 동기

현재 pydantic config class 는 field metadata 관리에 문제가 있다.

1. **version 정보 없음**: field 가 언제 추가되거나 지원이 중단됐는지 추적할 수 없다
2. **흩어진 문서**: `Field(description=...)` 와 그 밖의 metadata 가 따로 떨어져 있다
3. **환경별 example 없음**: local/prod 환경에 서로 다른 example 값을 제공할 수 없다

### 목표

- `Field` 는 **validation** 만 담당한다
- `BackendAIFieldMeta` 는 **문서화와 version 관리**를 맡는다
- `Annotated` 가 모든 metadata 를 한곳에 모은다

## 현재 설계

```python
class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(
        default="local",
        description="Namespace prefix for etcd keys.",
        examples=["local", "backend"],
    )
```

### 문제

1. version 정보를 추가할 수 없다
2. 환경별 example 을 구분할 수 없다
3. deprecated field 를 표시할 방법이 없다
4. secret 값 마스킹용 metadata 가 없다

## 제안 설계

### metadata class 구조

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

### field 정의 방식

`Annotated` 안에 `Field` 와 `Meta` 를 함께 지정한다.

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

### composite type 의 example 처리

child field 를 가진 composite type 은 `composite=True` 로 child field 에서 example 을 자동 생성한다.

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

### metadata 조회와 example 생성 utility

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

**생성된 example 결과:**

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

## field 요약

### BackendAIFieldMeta (공통)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `str` | ✓ | field 설명 |
| `added_version` | `str` | ✓ | 추가된 version |
| `deprecated_version` | `str \| None` | - | 지원이 중단된 version |
| `deprecation_hint` | `str \| None` | - | 마이그레이션 안내 |

### BackendAIConfigMeta (config)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `example` | `ConfigExample \| str \| None` | - | 환경별 example |
| `secret` | `bool` | - | 값의 secret 여부 (기본값: False) |
| `composite` | `bool` | - | child field 에서 example 생성 (기본값: False) |

### BackendAIAPIMeta (API)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `example` | `str \| None` | - | API 문서 example (문자열) |
| `composite` | `bool` | - | child field 에서 example 생성 (기본값: False) |

## 구현 계획

### Phase 1: metadata class 정의

**목표**: common module 에 metadata class 추가

**작업**:
- `src/ai/backend/common/config/meta.py` 생성
- `BackendAIFieldMeta`, `BackendAIConfigMeta`, `BackendAIAPIMeta` class 정의
- `ConfigExample` dataclass 정의
- metadata 조회 utility function 추가
- `composite` 기반 example 생성 function 추가

### Phase 2: config class 에 적용

**목표**: config class 에 `BackendAIConfigMeta` 적용

**대상 파일**:
- `src/ai/backend/manager/config/unified.py`
- `src/ai/backend/agent/config/unified.py`
- `src/ai/backend/storage/config/unified.py`
- `src/ai/backend/web/config/unified.py`
- `src/ai/backend/common/configs/*.py`

**예시**:
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

### Phase 3: API request/response 에 적용

**목표**: REST API DTO 에 `BackendAIAPIMeta` 적용

**대상 파일**:
- `src/ai/backend/manager/api/*/types.py`
- `src/ai/backend/manager/dto/*.py`

**예시**:
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

### Phase 4: strawberry GraphQL 에 적용

**목표**: GraphQL schema 에 `BackendAIAPIMeta` 적용

**대상 파일**:
- `src/ai/backend/manager/api/gql/*.py`
- `src/ai/backend/manager/models/gql_models/*.py`

**예시**:
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

**추가 작업**:
- `@strawberry.field(description=...)` 대신 Meta 에서 description 을 읽는 custom extension
- GraphQL schema 생성 시 `BackendAIAPIMeta` 에서 description 과 deprecation 정보를 자동으로 반영

### Phase 5: CLI, 문서 연동

**목표**: metadata 기반 자동화

**작업**:
- CLI `--help` 에 `BackendAIConfigMeta.description` 과 `example` 표시
- log 와 출력에서 `secret=True` field 를 마스킹
- `deprecated_version` 이 지정된 field 에 runtime warning 출력
- API 문서용 example 을 `composite` 방식에 따라 생성

## 참고

- [pydantic Annotated 방식](https://docs.pydantic.dev/latest/concepts/fields/#using-annotated)
- [Python typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
- [Strawberry GraphQL](https://strawberry.rocks/)
