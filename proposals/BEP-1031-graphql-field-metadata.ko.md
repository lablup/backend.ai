# BEP-1031: GraphQL API field metadata 확장

## 관련 이슈

- JIRA: [BA-3928](https://lablup.atlassian.net/browse/BA-3928)
- 관련 BEP: [BEP-1022: pydantic field metadata annotation](BEP-1022-pydantic-field-annotations.md)
- 관련 BEP: [BEP-1010: GraphQL API 를 Strawberry 로 이전](BEP-1010-new-gql.md)

## 동기

BEP-1022 는 API field metadata 관리를 위해 `BackendAIAPIMeta` 를 정의하고 Phase 4 에서 Strawberry GraphQL 통합을 언급했다. 그러나 Strawberry 의 type system 과 metadata 를 통합하는 구체적인 구현 방식은 정해지지 않았다.

### 현재 문제

1. **필수 metadata 가 빠질 수 있다**: version 정보는 description 에 포함해야 하지만 자유 형식 텍스트이므로 필수 값(version, deprecation 등)이 들어간다는 보장이 없다
2. **config 구조, REST API 와 일관되지 않다**: config 는 `BackendAIConfigMeta` 를 사용하고 REST API 는 `Annotated` 와 함께 `BackendAIAPIMeta` 를 사용하지만, GraphQL 은 문자열을 직접 사용한다
3. **deprecation 을 직접 처리한다**: metadata 로 `deprecation_reason` 을 자동 설정할 수 없다

### 목표

- `BackendAIAPIMeta` 를 Strawberry GraphQL 과 통합하는 구체적인 패턴 정의
- description 과 deprecation 을 자동으로 처리하는 utility function 제공
- BEP-1022 의 pydantic 기반 접근과 일관성 유지
- API 문서 자동 생성의 기반 마련

## 현재 설계

```python
@strawberry.type(
    description="Added in 26.1.0. User-level usage bucket..."
)
class UserUsageBucketGQL(Node):
    user_uuid: UUID = strawberry.field(
        description="UUID of the user this usage bucket belongs to."
    )
    # No version info, no structured metadata
```

### 문제

1. version 정보가 description 안의 자유 형식 텍스트다
2. version 정보를 프로그램으로 추출할 수 없다
3. field 마다 deprecation 을 직접 추가해야 한다
4. changelog 나 API 문서를 자동 생성할 수 없다

## 제안 설계

### 접근: wrapper function 과 decorator

Pydantic 과 달리 Strawberry 는 `Annotated` type 에서 metadata 를 자동으로 추출하지 않는다. 따라서 `BackendAIAPIMeta` 를 여러 Strawberry 구성 요소와 통합하는 wrapper 를 제공한다.

- `backend_ai_field()`: `strawberry.field()` wrapper - field 정의에 사용한다
- `backend_ai_type()`: `@strawberry.type` wrapper - 출력 type decorator
- `backend_ai_input()`: pydantic model 기반 input decorator - REST API 와 같은 validation 을 보장한다

### 핵심 구현

```python
# src/ai/backend/manager/api/gql/utils.py

from __future__ import annotations
from collections.abc import Callable, Sequence
from typing import Any

import strawberry
from pydantic import BaseModel
from strawberry.field import StrawberryField

from ai.backend.common.meta import BackendAIAPIMeta


def backend_ai_field(
    meta: BackendAIAPIMeta,
    *,
    name: str | None = None,
    default: Any = strawberry.UNSET,
    default_factory: Callable[[], Any] | None = None,
    init: bool = True,
    repr_: bool = True,
    hash_: bool | None = None,
    compare: bool = True,
    graphql_type: Any | None = None,
    permission_classes: list[type] | None = None,
    directives: Sequence[object] | None = None,
) -> StrawberryField:
    """Create a Strawberry field with BackendAI metadata.

    Automatically generates description with version prefix and
    sets deprecation_reason from metadata.

    Args:
        meta: BackendAI API metadata containing description, version, etc.
        name: GraphQL field name (if different from Python attribute)
        default: Field default value
        default_factory: Default value factory function
        init: Include in dataclass __init__
        repr_: Include in dataclass __repr__
        hash_: Include in dataclass __hash__
        compare: Include in dataclass comparison methods
        graphql_type: Explicit GraphQL type specification
        permission_classes: List of field access permission classes
        directives: List of GraphQL directives

    Returns:
        StrawberryField with integrated metadata

    Example:
        >>> user_uuid: UUID = backend_ai_field(
        ...     BackendAIAPIMeta(
        ...         description="UUID of the user",
        ...         added_version="26.1.0",
        ...     )
        ... )
    """
    # Generate description with version prefix
    description = f"Added in {meta.added_version}. {meta.description}"

    # Add deprecated marker if applicable
    if meta.deprecated_version:
        description = f"[Deprecated in {meta.deprecated_version}] {description}"

    # metadata is used internally by Strawberry for storing additional field info
    # - Enables programmatic version info extraction during introspection
    # - Used by API documentation generation tools
    # - Not exposed in GraphQL schema (server-side only)
    return strawberry.field(
        name=name,
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr_,
        hash=hash_,
        compare=compare,
        description=description,
        deprecation_reason=meta.deprecation_hint,
        graphql_type=graphql_type,
        permission_classes=permission_classes or [],
        directives=directives or (),
        metadata={"backend_ai_meta": meta},
    )


def backend_ai_type(
    meta: BackendAIAPIMeta,
    *,
    name: str | None = None,
    directives: Sequence[object] | None = None,
):
    """Strawberry type decorator with BackendAI metadata.

    Example:
        >>> @backend_ai_type(
        ...     BackendAIAPIMeta(
        ...         description="User-level usage bucket",
        ...         added_version="26.1.0",
        ...     )
        ... )
        ... class UserUsageBucketGQL(Node):
        ...     pass
    """
    description = f"Added in {meta.added_version}. {meta.description}"

    if meta.deprecated_version:
        description = f"[Deprecated in {meta.deprecated_version}] {description}"

    def decorator(cls):
        return strawberry.type(
            cls,
            name=name,
            description=description,
            directives=directives or (),
        )

    return decorator


def backend_ai_input(
    model: type[BaseModel],
    meta: BackendAIAPIMeta,
    *,
    name: str | None = None,
    all_fields: bool = True,
    directives: Sequence[object] | None = None,
):
    """Pydantic model-based Strawberry input decorator.

    Retrieves validation rules from Pydantic model and
    integrates version and description metadata from BackendAIAPIMeta.
    Input types always operate on Pydantic basis to ensure same validation as REST API.

    Args:
        model: Pydantic model with validation rules defined
        meta: BackendAI API metadata containing description, version, etc.
        name: GraphQL input type name (default: class name)
        all_fields: Whether to include all fields from Pydantic model
        directives: List of GraphQL directives

    Example:
        >>> @backend_ai_input(
        ...     model=CreateObjectStorageSpec,
        ...     meta=BackendAIAPIMeta(
        ...         description="Object Storage creation input",
        ...         added_version="25.14.0",
        ...     ),
        ... )
        ... class CreateObjectStorageInput:
        ...     pass
    """
    from strawberry.experimental import pydantic as strawberry_pydantic

    description = f"Added in {meta.added_version}. {meta.description}"

    def decorator(cls):
        return strawberry_pydantic.input(
            model=model,
            all_fields=all_fields,
            name=name,
            description=description,
            directives=directives or (),
        )(cls)

    return decorator
```

### 사용 예시

#### 출력 type

```python
from ai.backend.common.meta import BackendAIAPIMeta
from ai.backend.manager.api.gql.utils import backend_ai_type, backend_ai_field

@backend_ai_type(
    BackendAIAPIMeta(
        description="Bucket aggregating resource usage per user",
        added_version="26.1.0",
    )
)
class UserUsageBucketGQL(Node):
    id: NodeID[str]

    user_uuid: UUID = backend_ai_field(
        BackendAIAPIMeta(
            description="UUID of the user this usage bucket belongs to",
            added_version="26.1.0",
        )
    )

    project_id: UUID = backend_ai_field(
        BackendAIAPIMeta(
            description="UUID of the project the user belongs to",
            added_version="26.1.0",
        )
    )

    # Deprecated field example
    legacy_group_id: UUID | None = backend_ai_field(
        BackendAIAPIMeta(
            description="Legacy group identifier",
            added_version="25.1.0",
            deprecated_version="26.1.0",
            deprecation_hint="Use project_id instead",
        ),
        default=None,
    )
```

#### input type

```python
@backend_ai_input(
    model=CreateObjectStorageSpec,
    meta=BackendAIAPIMeta(
        description="Object Storage creation input",
        added_version="25.14.0",
    ),
)
class CreateObjectStorageInput:
    pass
```

#### mutation 과 query

```python
@strawberry.type
class Mutation:
    @backend_ai_field(
        BackendAIAPIMeta(
            description="Create new Object Storage configuration",
            added_version="25.14.0",
        )
    )
    async def create_object_storage(
        self,
        input: CreateObjectStorageInput,
        info: Info[StrawberryGQLContext],
    ) -> ObjectStorage:
        ...
```

### metadata 추출 utility

```python
# src/ai/backend/manager/api/gql/utils.py

def get_gql_field_meta(
    gql_type: type,
    field_name: str,
) -> BackendAIAPIMeta | None:
    """Extract BackendAIAPIMeta from Strawberry field.

    Useful for documentation generation and introspection tools.
    """
    strawberry_type = getattr(gql_type, '__strawberry_definition__', None)
    if strawberry_type is None:
        return None

    for field in strawberry_type.fields:
        if field.python_name == field_name:
            return field.metadata.get("backend_ai_meta")

    return None


def collect_all_field_versions(gql_type: type) -> dict[str, str]:
    """Collect version information for all fields in a type.

    Returns:
        Dict mapping field names to added_version
    """
    result = {}
    strawberry_type = getattr(gql_type, '__strawberry_definition__', None)
    if strawberry_type is None:
        return result

    for field in strawberry_type.fields:
        meta = field.metadata.get("backend_ai_meta")
        if meta:
            result[field.python_name] = meta.added_version

    return result
```

### 생성되는 GraphQL schema

wrapper function 은 version 정보를 담은 표준 GraphQL schema 를 생성한다.

```graphql
"""
Added in 26.1.0. Bucket aggregating resource usage per user
"""
type UserUsageBucket implements Node {
  id: ID!

  """
  Added in 26.1.0. UUID of the user this usage bucket belongs to
  """
  userUuid: UUID!

  """
  Added in 26.1.0. UUID of the project the user belongs to
  """
  projectId: UUID!

  """
  [Deprecated in 26.1.0] Added in 25.1.0. Legacy group identifier
  """
  legacyGroupId: UUID @deprecated(reason: "Use project_id instead")
}
```

## 이전 / 호환성

### 하위 호환성

- 기존 `strawberry.field(description=...)` 패턴은 계속 동작한다
- 새 패턴은 선택 사항이며 점진적으로 적용할 수 있다
- GraphQL schema 출력에 breaking change 가 없다

### 이전 전략

1. 새 type 과 field 는 `backend_ai_field()` 와 `backend_ai_type()` 을 사용한다
2. 기존 type 은 수정할 때 점진적으로 이전한다
3. 한 번에 모두 이전할 필요가 없다

### 공존 예시

```python
@strawberry.type(description="Added in 25.14.0. Legacy type")
class LegacyType:
    # Existing pattern - continues to work
    old_field: str = strawberry.field(description="Added in 25.14.0. Existing field")

    # New pattern
    new_field: str = backend_ai_field(
        BackendAIAPIMeta(
            description="New field with structured metadata",
            added_version="26.1.0",
        )
    )
```

## 구현 계획

### Phase 1: 핵심 utility

**목표**: wrapper function 구현

**작업**:
- `backend_ai_field()` 를 `src/ai/backend/manager/api/gql/utils.py` 에 추가
- `backend_ai_type()` decorator 추가
- `backend_ai_input()` decorator 추가
- metadata 추출 utility 추가
- 단위 테스트 추가

### Phase 2: 새 type 에 적용

**목표**: 모든 새 GraphQL type 에 새 패턴 사용

**작업**:
- 코딩 가이드라인을 수정해 새 패턴을 권장
- 개발 중인 새 type 에 적용
- `api/gql/README.md` 에 문서화

### Phase 3: 점진적 이전

**목표**: 기존 type 을 수정할 때 이전

**작업**:
- 이전 체크리스트 작성
- 다른 이유로 수정하는 type 을 이전
- 이전 진행 상황 추적

### Phase 4: 도구 통합

**목표**: metadata 를 문서에 활용

**작업**:
- version metadata 로 API changelog 생성
- deprecation 보고서 생성
- API 문서 도구와 통합

## 열린 질문

1. 모든 field 에 metadata 가 있는지 자동으로 검사하는 schema extension 생성 여부
2. wrapper function 외에 `Annotated` type 에서 metadata 를 추출하는 기능의 지원 여부
3. base class 에서 상속한 field(예: `Node.id`)를 처리하는 방식

## 참고

- [BEP-1022: pydantic field metadata annotation](BEP-1022-pydantic-field-annotations.md)
- [BEP-1010: GraphQL API 를 Strawberry 로 이전](BEP-1010-new-gql.md)
- [Strawberry GraphQL Field API](https://strawberry.rocks/api-reference/strawberry.field)
- [Strawberry Field Extensions](https://strawberry.rocks/docs/guides/field-extensions)
