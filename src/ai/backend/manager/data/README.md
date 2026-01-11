# Manager Component-Internal DTOs

This module contains Data Transfer Objects (DTOs) that are used exclusively within the Manager component.

## Purpose

DTOs in `ai.backend.manager.data` are internal data structures for:
- Service layer operations
- Repository layer query results
- Domain-specific aggregations
- Internal business logic data flow

These DTOs are **NOT** exposed to other components through RPC or REST APIs.

## Organization

DTOs are organized by domain:

```
data/
├── deployment/         # Deployment domain DTOs
├── session/           # Session management DTOs
├── user/              # User management DTOs
├── agent/             # Agent-related DTOs (internal)
├── vfolder/           # Virtual folder DTOs
├── notification/      # Notification DTOs
├── auth/              # Authentication DTOs (internal)
└── ...                # Other domains
```

Each domain directory contains DTOs specific to that domain's internal operations.

## When to Add DTOs Here

**✅ Add to `manager/data/` when:**
- The DTO is used only within Manager's service layer
- The DTO is used only within Manager's repository layer
- The DTO represents internal business logic data structures
- The DTO is a query result from repositories
- No other component needs to reference it
- Changes affect only the Manager component

**❌ Do NOT add to `manager/data/` when:**
- The DTO is exposed through REST API to external clients
- The DTO is used in RPC calls to Agent or Storage
- The DTO is part of GraphQL schema consumed by web UI
- Other components need the same data structure

For inter-component DTOs, use `ai.backend.common.dto/manager/` instead.

**Note on `ai.backend.manager.dto/`:**
- This is a legacy module for inter-component communication
- Use Pydantic models in `manager.dto/` for now
- Gradually migrate DTOs to `common/dto/manager/` for better type sharing across components

## Guidelines

### 1. Use Dataclasses for Internal DTOs

Prefer dataclasses for simplicity and performance in internal DTOs:

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class DeploymentScaleConfig:
    """Internal configuration for deployment scaling.

    Used by the service layer to coordinate with the sokovan layer.
    """

    min_replicas: int
    max_replicas: int
    target_cpu_utilization: float
    cooldown_period: int
```

### 2. Immutability

DTOs should be immutable to prevent unintended side effects:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionResourceAllocation:
    """Resource allocation for a session (internal)."""

    session_id: str
    resource_slots: tuple[str, ...]  # Use tuple, not list
    device_ids: tuple[int, ...] = ()
```

### 3. Postel's Law for Type Hints

Follow Postel's Law in function signatures that use these DTOs:

```python
from collections.abc import Sequence

# Accept abstract types
def process_sessions(sessions: Sequence[SessionResourceAllocation]) -> list[str]:
    """Process multiple session allocations.

    Args:
        sessions: Sequence of session allocations (accepts list, tuple, etc.)

    Returns:
        List of session IDs (concrete type for clarity)
    """
    return [s.session_id for s in sessions]
```

### 4. Documentation

All DTOs must have:
- Class docstring explaining the purpose and usage context
- Field annotations with types
- Docstrings or comments for non-obvious fields

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelRevisionConfig:
    """Configuration for a model deployment revision.

    Used internally by the deployment service to track
    revision-specific settings before creating database records.
    """

    deployment_id: str
    revision_number: int
    model_path: str
    runtime_config: dict[str, str]  # Framework-specific parameters
    created_by: str  # User ID who created this revision
```

### 5. Type Hints

Always provide comprehensive type hints:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment import DeploymentRepository

@dataclass(frozen=True)
class DeploymentCreationContext:
    """Context for creating a deployment (internal).

    Aggregates all information needed for the creation process.
    """

    deployment_id: str
    owner_id: str
    project_id: str
    config: DeploymentScaleConfig
    # Repository reference for internal operations
    repository: DeploymentRepository
```

### 6. None Checking

Always use explicit identity checks:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionFilter:
    project_id: str | None = None
    user_id: str | None = None

def apply_filter(filter: SessionFilter) -> str:
    conditions = []

    # CORRECT: Use explicit None checks
    if filter.project_id is not None:
        conditions.append(f"project_id = {filter.project_id}")

    if filter.user_id is not None:
        conditions.append(f"user_id = {filter.user_id}")

    return " AND ".join(conditions)
```

## Domain-Specific Directories

### deployment/
Internal DTOs for the deployment domain.

Examples:
- Scale configurations
- Revision metadata
- Internal deployment states
- Access token internal data

**Note:** Public deployment APIs use `ai.backend.common.dto/manager/` DTOs.

### session/
Internal DTOs for session management.

Examples:
- Resource allocation results
- Session lifecycle state transitions
- Internal session metadata

### user/
Internal DTOs for user management operations.

Examples:
- User query results
- Internal user preferences
- Permission aggregations

### notification/
Internal DTOs for notification processing.

Examples:
- Notification dispatch context
- Channel-specific payloads
- Internal notification state

## Relationship with Other Layers

```
┌─────────────────────────────────────────────────────────────┐
│ External Clients (Web UI, CLI)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST/GraphQL API
                      │ (uses common/dto/manager)
┌─────────────────────▼───────────────────────────────────────┐
│ API Layer (api/gql/*)                                        │
│   - Converts between API DTOs and Internal DTOs             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Service Layer (services/*)                                   │
│   - Uses manager/data DTOs internally                        │
│   - Business logic operates on internal DTOs                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Repository Layer (repositories/*)                            │
│   - Returns manager/data DTOs as query results               │
│   - Converts between DB models and internal DTOs            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Database Models (models/*)                                   │
└─────────────────────────────────────────────────────────────┘
```

## Examples

### Good Example: Internal DTO

```python
# src/ai/backend/manager/data/deployment/scale.py
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ScaleOperationContext:
    """Internal context for scaling operations.

    Used by the deployment service to coordinate scaling
    between the service layer and sokovan layer.
    """

    deployment_id: str
    current_replicas: int
    desired_replicas: int
    scaling_policy: str
    initiated_by: str  # user_id or "system"
```

### Bad Example: Should be in common/dto

```python
# ❌ WRONG: This is exposed through GraphQL API
# Should be in ai.backend.common.dto/manager/response.py

from pydantic import BaseModel

class DeploymentStatusResponse(BaseModel):
    """Deployment status for GraphQL API."""  # This is external!

    deployment_id: str
    state: str
    replicas: int
```

### Migration Example

When an internal DTO needs to be exposed externally:

```python
# Before: In manager/data/deployment/status.py
@dataclass(frozen=True)
class InternalDeploymentStatus:
    deployment_id: str
    state: str
    replicas: int
    internal_notes: str  # Internal field

# After: In common/dto/manager/response.py
class DeploymentStatusResponse(BaseModel):
    """Deployment status exposed through API."""

    deployment_id: str
    state: str
    replicas: int
    # internal_notes removed - not exposed externally

# The internal DTO can remain for service layer use
```

## See Also

- [Shared DTOs README](../../common/dto/README.md) - Inter-component DTOs
- [Manager README](../README.md) - Manager component overview
