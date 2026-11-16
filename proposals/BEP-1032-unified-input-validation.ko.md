# BEP-1032: REST 와 GraphQL 의 통합 input 검증

## 관련 이슈

- JIRA: [BA-3928](https://lablup.atlassian.net/browse/BA-3928)
- 관련 BEP: [BEP-1022: pydantic field metadata annotation](BEP-1022-pydantic-field-annotations.md)
- 관련 BEP: [BEP-1031: GraphQL API field metadata 확장](BEP-1031-graphql-field-metadata.md)
- 관련 BEP: [BEP-1010: 새 GQL](BEP-1010-new-gql.md)

## 동기

현재 REST API 와 GraphQL API 는 같은 도메인 로직에 대해 각자 검증을 구현한다. 이 때문에 다음 문제가 생긴다.

### 현재 문제

1. **검증 로직 중복**: 같은 field 에 대해 REST 와 GraphQL 에 검증을 따로 작성한다
2. **일관성 부족**: 한쪽에서 검증 규칙을 변경하면 다른 쪽에서 놓칠 수 있다
3. **테스트 부담**: 같은 검증을 두 곳에서 테스트해야 한다
4. **유지 비용**: business rule 이 바뀌면 두 곳을 모두 수정해야 한다

### 목표

- 검증 규칙을 하나의 pydantic model 에 정의한다
- REST API 와 GraphQL API 에 같은 검증을 적용한다
- `BackendAIAPIMeta` 로 metadata 를 통합한다
- 코드 중복을 제거하고 유지보수성을 높인다

## 현재 설계

### REST API (pydantic 직접 사용)

```python
# src/ai/backend/manager/dto/request.py
from pydantic import Field
from ai.backend.common.api_handlers import BaseRequestModel

class CreateObjectStorageRequest(BaseRequestModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(pattern=r'^[\w.-]+(:\d+)?$')
    access_key: str = Field(min_length=10)
    secret_key: str = Field(min_length=10)
```

### GraphQL API (Strawberry 직접 사용)

```python
# src/ai/backend/manager/api/gql/object_storage.py
import strawberry

@strawberry.input(description="Added in 25.14.0")
class CreateObjectStorageInput:
    name: str  # No validation
    host: str  # No validation
    access_key: str  # No validation
    secret_key: str  # No validation
```

### 문제

1. GraphQL input 에 검증이 없거나 검증을 따로 구현해야 한다
2. 검증 규칙이 REST 와 GraphQL 에서 달라질 수 있다
3. `BackendAIAPIMeta` metadata 를 공유하지 않는다

## 제안 설계

### 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Pydantic Spec                      │
│              (validation + BackendAIAPIMeta)                 │
│                                                              │
│  src/ai/backend/common/dto/manager/{domain}/shared.py       │
└─────────────────────┬───────────────────┬───────────────────┘
                      │                   │
         ┌────────────▼────────┐  ┌───────▼────────────────┐
         │      REST API       │  │       GraphQL          │
         │                     │  │                        │
         │  Direct usage       │  │  backend_ai_input()    │
         │  (BaseRequestModel) │  │  conversion            │
         └─────────────────────┘  └────────────────────────┘
```

### 공유 pydantic spec 정의

```python
# src/ai/backend/common/dto/manager/object_storage/shared.py

from __future__ import annotations
from typing import Annotated
from pydantic import Field, field_validator
from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.meta import BackendAIAPIMeta


class CreateObjectStorageSpec(BaseRequestModel):
    """Object Storage creation request spec.

    Shared validation and metadata definition for REST API and GraphQL API.
    """

    name: Annotated[
        str,
        Field(min_length=1, max_length=100),
        BackendAIAPIMeta(
            description="Unique name for Object Storage",
            added_version="25.14.0",
        ),
    ]

    host: Annotated[
        str,
        Field(pattern=r'^[\w.-]+(:\d+)?$'),
        BackendAIAPIMeta(
            description="Host address including port (e.g., s3.example.com:9000)",
            added_version="25.14.0",
        ),
    ]

    access_key: Annotated[
        str,
        Field(min_length=10),
        BackendAIAPIMeta(
            description="S3-compatible Access Key",
            added_version="25.14.0",
            secret=True,
        ),
    ]

    secret_key: Annotated[
        str,
        Field(min_length=10),
        BackendAIAPIMeta(
            description="S3-compatible Secret Key",
            added_version="25.14.0",
            secret=True,
        ),
    ]

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Name validation: cannot start with underscore."""
        if v.startswith('_'):
            raise ValueError("Name cannot start with underscore")
        return v


class UpdateObjectStorageSpec(BaseRequestModel):
    """Object Storage update request spec."""

    name: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=100),
        BackendAIAPIMeta(
            description="New name for Object Storage",
            added_version="25.14.0",
        ),
    ]

    host: Annotated[
        str | None,
        Field(default=None, pattern=r'^[\w.-]+(:\d+)?$'),
        BackendAIAPIMeta(
            description="New host address",
            added_version="25.14.0",
        ),
    ]
```

### GraphQL input 생성 (strawberry.experimental.pydantic)

```python
# src/ai/backend/manager/api/gql/object_storage/inputs.py

from __future__ import annotations

from ai.backend.common.dto.manager.object_storage.shared import (
    CreateObjectStorageSpec,
    UpdateObjectStorageSpec,
)
from ai.backend.common.meta import BackendAIAPIMeta


# Use backend_ai_input() from BEP-1031 to integrate metadata + validation
# Input types always operate on Pydantic basis

from ai.backend.manager.api.gql.utils import backend_ai_input

@backend_ai_input(
    model=CreateObjectStorageSpec,
    meta=BackendAIAPIMeta(
        description="Object Storage creation input",
        added_version="25.14.0",
    ),
)
class CreateObjectStorageInput:
    """GraphQL Input auto-generated from Pydantic Spec."""
    pass


@backend_ai_input(
    model=UpdateObjectStorageSpec,
    meta=BackendAIAPIMeta(
        description="Object Storage update input",
        added_version="25.14.0",
    ),
)
class UpdateObjectStorageInput:
    """GraphQL Input auto-generated from Pydantic Spec."""
    pass
```

### GraphQL mutation 에서 사용

```python
# src/ai/backend/manager/api/gql/object_storage/mutations.py

import strawberry
from pydantic import ValidationError
from strawberry.types import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors import InvalidAPIParameterError
from .inputs import CreateObjectStorageInput
from .types import ObjectStorage


@strawberry.type
class ObjectStorageMutation:

    @strawberry.mutation(description="Added in 25.14.0. Create new Object Storage")
    async def create_object_storage(
        self,
        input: CreateObjectStorageInput,
        info: Info[StrawberryGQLContext],
    ) -> ObjectStorage:
        # Pydantic validation executed on to_pydantic() call
        # Same validation rules as REST API applied
        try:
            spec = input.to_pydantic()  # Returns CreateObjectStorageSpec
        except ValidationError as e:
            # Convert Pydantic ValidationError to BackendAIError
            raise InvalidAPIParameterError.from_validation_error("input", e)

        # Execute business logic
        result = await info.context.services.object_storage.create(spec)
        return ObjectStorage.from_data(result)
```

### REST API 에서 사용

```python
# src/ai/backend/manager/api/object_storage.py

from aiohttp import web

from ai.backend.common.dto.manager.object_storage.shared import CreateObjectStorageSpec


async def create_object_storage(request: web.Request) -> web.Response:
    """REST API: Create Object Storage."""
    body = await request.json()

    # Pydantic validation executed (same Spec as GraphQL)
    spec = CreateObjectStorageSpec.model_validate(body)

    # Execute business logic
    services = request.app['services']
    result = await services.object_storage.create(spec)

    return web.json_response(result.model_dump())
```

### 검증 자동화를 위한 Field Extension (선택)

매번 `to_pydantic()` 을 호출하는 일을 자동화하려면 Field Extension 을 사용한다.

```python
# src/ai/backend/manager/api/gql/extensions.py

from typing import Any, Callable, Protocol, TypeVar, runtime_checkable
from pydantic import BaseModel, ValidationError
import strawberry
from strawberry.extensions import FieldExtension
from strawberry.types import Info

from ai.backend.manager.errors import InvalidAPIParameterError

T = TypeVar('T', bound=BaseModel)


@runtime_checkable
class PydanticConvertible(Protocol[T]):
    """Protocol for Strawberry input types convertible to Pydantic models."""
    def to_pydantic(self) -> T: ...


class PydanticValidationExtension(FieldExtension):
    """Automatically convert GraphQL input to Pydantic model with validation."""

    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: Info,
        **kwargs: Any,
    ) -> Any:
        # Automatically call to_pydantic() on Input types
        validated_kwargs = {}
        for key, value in kwargs.items():
            # Type check using Protocol (more explicit than hasattr)
            if isinstance(value, PydanticConvertible):
                try:
                    validated_kwargs[key] = value.to_pydantic()
                except ValidationError as e:
                    # Convert ValidationError to BackendAIError
                    raise InvalidAPIParameterError.from_validation_error(key, e)
            else:
                validated_kwargs[key] = value

        return next_(source, info, **validated_kwargs)


# Usage example
@strawberry.mutation(extensions=[PydanticValidationExtension()])
async def create_object_storage(
    self,
    input: CreateObjectStorageInput,  # Automatically converted to CreateObjectStorageSpec
    info: Info[StrawberryGQLContext],
) -> ObjectStorage:
    # input is already a Pydantic model (CreateObjectStorageSpec)
    spec: CreateObjectStorageSpec = input
    ...
```

### 디렉터리 구조

기존 `src/ai/backend/common/dto/manager/` 의 Request, Response, Shared 분리 패턴을 따른다.

```
src/ai/backend/common/dto/manager/
├── object_storage/
│   ├── __init__.py
│   ├── shared.py             # Shared Pydantic models (validation + meta)
│   │                         # Spec definitions shared by REST and GraphQL
│   ├── request.py            # REST API request models (using shared)
│   └── response.py           # REST API response models
│
└── {other_domain}/
    ├── shared.py             # Shared validation rules
    ├── request.py
    └── response.py

src/ai/backend/manager/
├── api/
│   ├── object_storage.py     # REST API handlers
│   └── gql/
│       ├── extensions.py     # PydanticValidationExtension
│       └── object_storage/
│           ├── __init__.py
│           ├── inputs.py     # GraphQL inputs (generated from shared.py Spec)
│           ├── types.py      # GraphQL output types
│           └── mutations.py  # GraphQL mutations
│
└── dto/                      # (Backward compatibility, re-export only)
    └── object_storage.py     # Re-export from common/dto
```

**핵심 원칙**:
- `shared.py`: REST/GraphQL 공유 검증 규칙과 `BackendAIAPIMeta` 정의
- `request.py`: REST API 전용 request model (공유 spec 을 사용하거나 확장한다)
- `response.py`: REST API 전용 response model
- GraphQL input: `shared.py` 의 spec 을 `backend_ai_input()` 으로 변환한다

### 기존 코드와의 호환성

기존 `dto/` 디렉터리의 model 은 re-export 로 유지한다.

```python
# src/ai/backend/manager/dto/object_storage.py

# Re-export for backward compatibility
from ai.backend.common.dto.manager.object_storage.shared import (
    CreateObjectStorageSpec as CreateObjectStorageRequest,
    UpdateObjectStorageSpec as UpdateObjectStorageRequest,
)

__all__ = [
    "CreateObjectStorageRequest",
    "UpdateObjectStorageRequest",
]
```

## 검증 에러 처리

### BackendAIError 기반 에러 정의

input 검증 실패에는 `BackendAIError` 를 상속한 전용 에러를 사용한다.

```python
# src/ai/backend/manager/errors.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ai.backend.common.exception import BackendAIError


@dataclass
class ValidationErrorDetail:
    """Represents individual error from Pydantic ValidationError as a value."""
    field: str
    message: str
    type: str
    input_value: Any = None

    @classmethod
    def from_pydantic_error(cls, error: dict[str, Any]) -> ValidationErrorDetail:
        """Create from Pydantic error dict."""
        return cls(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            type=error["type"],
            input_value=error.get("input"),
        )


@dataclass
class InvalidAPIParameterError(BackendAIError):
    """API parameter validation failure error.

    Converts Pydantic ValidationError to BackendAIError for
    consistent error handling and error access as values.
    """
    parameter_name: str
    errors: list[ValidationErrorDetail] = field(default_factory=list)

    @classmethod
    def from_validation_error(
        cls,
        parameter_name: str,
        validation_error: ValidationError,
    ) -> InvalidAPIParameterError:
        """Create from Pydantic ValidationError.

        Catches ValidationError and converts to BackendAIError system.
        Error details are structured and preserved as ValidationErrorDetail.
        """
        details = [
            ValidationErrorDetail.from_pydantic_error(err)
            for err in validation_error.errors()
        ]
        return cls(parameter_name=parameter_name, errors=details)

    def __str__(self) -> str:
        messages = [f"{e.field}: {e.message}" for e in self.errors]
        return f"Validation failed for '{self.parameter_name}': {'; '.join(messages)}"


# Usage example
try:
    spec = input.to_pydantic()
except ValidationError as e:
    # Convert ValidationError to BackendAIError that can be handled as a value
    raise InvalidAPIParameterError.from_validation_error("input", e)
```

### GraphQL 에러 응답 변환

```python
# src/ai/backend/manager/api/gql/utils.py

def format_validation_error_for_graphql(error: InvalidAPIParameterError) -> str:
    """Format InvalidAPIParameterError as GraphQL error message."""
    return str(error)
```

### GraphQL 에러 응답 예시

```json
{
  "errors": [
    {
      "message": "Validation failed for 'input': name: Name cannot start with underscore; access_key: String should have at least 10 characters",
      "path": ["createObjectStorage"]
    }
  ]
}
```

## 이전 / 호환성

### 호환성

- 기존 `dto/` model 은 alias 로 계속 사용할 수 있다
- GraphQL schema 출력에 변화가 없다 (description 은 그대로다)
- REST API 응답 형식에 변화가 없다

### 이전 전략

1. **Phase 1**: 새 도메인은 `common/dto/manager/{domain}/shared.py` 패턴을 사용한다
2. **Phase 2**: 기존 도메인은 수정할 때 점진적으로 이전한다
3. **Phase 3**: `manager/dto/` 디렉터리는 re-export 만 두고 실제 model 은 `common/dto/` 로 옮긴다

### 호환성을 깨는 변경

- 없음 (완전한 하위 호환)

## 구현 계획

### Phase 1: 기반 구성

**목표**: 기본 패턴과 utility 를 구현한다

**작업**:
- `PydanticValidationExtension` 구현
- `InvalidAPIParameterError` 와 utility 추가
- 패턴 문서화

### Phase 2: 시범 적용

**목표**: 한 도메인에 새 패턴을 적용한다

**대상**: `object_storage` (비교적 단순한 도메인)

**작업**:
- `common/dto/manager/object_storage/shared.py` 생성
- GraphQL input 이전
- REST API 이전
- 테스트 통합

### Phase 3: 새 도메인에 적용

**목표**: 모든 새 도메인에 적용한다

**작업**:
- 코딩 가이드라인에 패턴 추가
- code review checklist 수정

### Phase 4: 기존 도메인 이전

**목표**: 기존 도메인을 점진적으로 이전한다

**우선순위**:
1. 자주 수정하는 도메인
2. 검증이 복잡한 도메인
3. REST 와 GraphQL 이 일관되지 않은 도메인

## 이점 요약

| 항목 | 설명 |
|------|-------------|
| **검증 통합** | 모든 검증을 하나의 pydantic model 에서 관리한다 |
| **metadata 통합** | version, description 을 `BackendAIAPIMeta` 로 관리한다 |
| **코드 중복 제거** | REST/GraphQL 에 검증 로직을 따로 작성할 필요가 없다 |
| **일관성 보장** | 같은 규칙을 양쪽에 자동으로 적용한다 |
| **테스트 단순화** | pydantic model 을 테스트하면 양쪽을 함께 검증한다 |
| **유지보수성** | business rule 이 바뀌면 한 곳만 수정한다 |

## 열린 질문

1. `strawberry.experimental.pydantic` 의 production 사용 가능 여부 (현재 experimental 상태다)
2. pydantic 의 constrained type (예: `constr(min_length=1)`) 을 GraphQL schema 에 노출할 필요가 있는지
3. 중첩 검증(복잡한 객체)의 에러 메시지 형식 결정
4. `PydanticValidationExtension` 의 전역 적용과 mutation 별 적용 중 선택

## 참고

- [BEP-1022: pydantic field metadata annotation](BEP-1022-pydantic-field-annotations.md)
- [BEP-1031: GraphQL API field metadata 확장](BEP-1031-graphql-field-metadata.md)
- [Strawberry Pydantic Integration](https://strawberry.rocks/docs/integrations/pydantic)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
