---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-01-17
Created-Version: 26.1.0
Target-Version:
Implemented-Version:
---

# BEP-1031: GraphQL API Field Metadata Extension

## Related Issues

- JIRA: [BA-3928](https://lablup.atlassian.net/browse/BA-3928)
- Related BEP: [BEP-1022: Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)
- Related BEP: [BEP-1010: New GQL](BEP-1010-new-gql.md)

## Motivation

BEP-1022 defined `BackendAIAPIMeta` for API field metadata management and mentioned Strawberry GraphQL integration in Phase 4. However, the specific implementation method for integrating Strawberry's type system with metadata was not specified.

### Current Problems

1. **Required metadata may be missing**: Version information should be included in description, but since it's free-form text, there's no guarantee that required values (version, deprecation, etc.) are included
2. **Inconsistency with Config structure and REST API**: Config uses `BackendAIConfigMeta`, REST API uses `BackendAIAPIMeta` with `Annotated`, but GraphQL uses strings directly
3. **Manual deprecation handling**: Cannot automatically set deprecation_reason from metadata

### Goals

- Define specific patterns for integrating `BackendAIAPIMeta` with Strawberry GraphQL
- Provide utility functions for automatic description and deprecation handling
- Maintain consistency with BEP-1022's Pydantic-based approach
- Establish foundation for automatic API documentation generation

## Current Design

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

### Problems

1. Version information is free-form text within description
2. Cannot programmatically extract version information
3. Must manually add deprecation for each field
4. Cannot auto-generate changelog or API documentation

## Proposed Design

### Approach: Custom Wrapper Functions and Decorators

Unlike Pydantic, Strawberry does not automatically extract metadata from `Annotated` types. Therefore, we provide wrappers that integrate `BackendAIAPIMeta` with various Strawberry components:

- `backend_ai_field()`: `strawberry.field()` wrapper - for field definitions
- `backend_ai_type()`: `@strawberry.type` wrapper - Output type decorator
- `backend_ai_input()`: Pydantic model-based Input decorator - ensures same validation as REST API

### Core Implementation

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

### Usage Examples

#### Output Types

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

#### Input Types

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

#### Mutations and Queries

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

### Metadata Extraction Utilities

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

### Generated GraphQL Schema

The wrapper functions generate standard GraphQL schema with version information:

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

## Migration / Compatibility

### Backward Compatibility

- Existing `strawberry.field(description=...)` pattern continues to work
- New pattern is opt-in and can be applied gradually
- No breaking changes in GraphQL schema output

### Migration Strategy

1. New types/fields use `backend_ai_field()` and `backend_ai_type()`
2. Existing types are gradually migrated when modified
3. No need to migrate everything at once

### Coexistence Example

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

## Implementation Plan

### Phase 1: Core Utilities

**Goal**: Implement wrapper functions

**Tasks**:
- Add `backend_ai_field()` to `src/ai/backend/manager/api/gql/utils.py`
- Add `backend_ai_type()` decorator
- Add `backend_ai_input()` decorator
- Add metadata extraction utilities
- Add unit tests

### Phase 2: Apply to New Types

**Goal**: Use new pattern for all new GraphQL types

**Tasks**:
- Update coding guidelines to recommend new pattern
- Apply to new types under development
- Document in `api/gql/README.md`

### Phase 3: Gradual Migration

**Goal**: Migrate existing types when modified

**Tasks**:
- Create migration checklist
- Update types when modified for other reasons
- Track migration progress

### Phase 4: Tooling Integration

**Goal**: Leverage metadata for documentation

**Tasks**:
- Generate API changelog from version metadata
- Generate deprecation reports
- Integrate with API documentation tools

## Open Questions

1. Should we create a schema extension that automatically validates all fields have metadata?
2. Should we support metadata extraction from `Annotated` types in addition to wrapper functions?
3. How should we handle fields inherited from base classes (e.g., `Node.id`)?

## References

- [BEP-1022: Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)
- [BEP-1010: New GQL](BEP-1010-new-gql.md)
- [Strawberry GraphQL Field API](https://strawberry.rocks/api-reference/strawberry.field)
- [Strawberry Field Extensions](https://strawberry.rocks/docs/guides/field-extensions)
