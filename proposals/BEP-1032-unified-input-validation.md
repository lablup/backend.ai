---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-01-17
Created-Version: 26.1.0
Target-Version:
Implemented-Version:
---

# BEP-1032: Unified Input Validation for REST and GraphQL

## Related Issues

- JIRA: [BA-3928](https://lablup.atlassian.net/browse/BA-3928)
- Related BEP: [BEP-1022: Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)
- Related BEP: [BEP-1031: GraphQL API Field Metadata Extension](BEP-1031-graphql-field-metadata.md)
- Related BEP: [BEP-1010: New GQL](BEP-1010-new-gql.md)

## Motivation

Currently, REST API and GraphQL API implement separate validation for the same domain logic. This causes the following problems:

### Current Problems

1. **Duplicate validation logic**: Writing validation separately for REST and GraphQL for the same fields
2. **Lack of consistency**: When validation rules change on one side, they may be missed on the other
3. **Testing burden**: Must test the same validation in two places
4. **Maintenance cost**: Must modify both places when business rules change

### Goals

- Define validation rules in a single Pydantic model
- Apply the same validation to both REST API and GraphQL API
- Integrate metadata through `BackendAIAPIMeta`
- Eliminate code duplication and improve maintainability

## Current Design

### REST API (Using Pydantic directly)

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

### GraphQL API (Using Strawberry directly)

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

### Problems

1. GraphQL input has no validation or requires separate implementation
2. Validation rules may differ between REST and GraphQL
3. `BackendAIAPIMeta` metadata is not shared

## Proposed Design

### Architecture Overview

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

### Shared Pydantic Spec Definition

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

### GraphQL Input Generation (strawberry.experimental.pydantic)

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

### Using in GraphQL Mutation

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

### Using in REST API

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

### Field Extension for Validation Automation (Optional)

To automate calling `to_pydantic()` every time, use Field Extension:

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

### Directory Structure

Following the existing `src/ai/backend/common/dto/manager/` pattern with Request, Response, Shared separation:

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

**Core Principles**:
- `shared.py`: REST/GraphQL shared validation rules and `BackendAIAPIMeta` definitions
- `request.py`: REST API-specific request models (using or extending shared Spec)
- `response.py`: REST API-specific response models
- GraphQL inputs: Convert `shared.py` Spec using `backend_ai_input()`

### Backward Compatibility with Existing Code

Existing `dto/` directory models maintained as re-exports:

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

## Validation Error Handling

### BackendAIError-based Error Definition

Use dedicated error inheriting from `BackendAIError` for input validation failures:

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

### GraphQL Error Response Conversion

```python
# src/ai/backend/manager/api/gql/utils.py

def format_validation_error_for_graphql(error: InvalidAPIParameterError) -> str:
    """Format InvalidAPIParameterError as GraphQL error message."""
    return str(error)
```

### GraphQL Error Response Example

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

## Migration / Compatibility

### Backward Compatibility

- Existing `dto/` models can continue to be used as aliases
- No changes in GraphQL schema output (description remains the same)
- No changes in REST API response format

### Migration Strategy

1. **Phase 1**: New domains use `common/dto/manager/{domain}/shared.py` pattern
2. **Phase 2**: Existing domains are gradually migrated when modified
3. **Phase 3**: `manager/dto/` directory maintains re-exports only, actual models move to `common/dto/`

### Breaking Changes

- None (full backward compatibility)

## Implementation Plan

### Phase 1: Foundation Setup

**Goal**: Implement basic patterns and utilities

**Tasks**:
- Implement `PydanticValidationExtension`
- Add `InvalidAPIParameterError` and utilities
- Document patterns

### Phase 2: Pilot Application

**Goal**: Apply new pattern to one domain

**Target**: `object_storage` (relatively simple domain)

**Tasks**:
- Create `common/dto/manager/object_storage/shared.py`
- Migrate GraphQL inputs
- Migrate REST API
- Integrate tests

### Phase 3: Apply to New Domains

**Goal**: Apply to all new domains

**Tasks**:
- Add pattern to coding guidelines
- Update code review checklist

### Phase 4: Migrate Existing Domains

**Goal**: Gradually migrate existing domains

**Priority**:
1. Frequently modified domains
2. Domains with complex validation
3. Domains with REST/GraphQL inconsistencies

## Benefits Summary

| Item | Description |
|------|-------------|
| **Unified validation** | Manage all validation in a single Pydantic model |
| **Integrated metadata** | Manage version, description with `BackendAIAPIMeta` |
| **Code deduplication** | No need to write validation logic separately for REST/GraphQL |
| **Consistency guarantee** | Same rules automatically applied to both sides |
| **Simplified testing** | Testing Pydantic model covers both sides |
| **Maintainability** | Only one place to modify when business rules change |

## Open Questions

1. Is `strawberry.experimental.pydantic` production-ready? (Currently experimental status)
2. Should Pydantic's constrained types (e.g., `constr(min_length=1)`) be exposed in GraphQL schema?
3. What should be the error message format for nested validation (complex objects)?
4. Should `PydanticValidationExtension` be applied globally or per-mutation?

## References

- [BEP-1022: Pydantic Field Metadata Annotation](BEP-1022-pydantic-field-annotations.md)
- [BEP-1031: GraphQL API Field Metadata Extension](BEP-1031-graphql-field-metadata.md)
- [Strawberry Pydantic Integration](https://strawberry.rocks/docs/integrations/pydantic)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
