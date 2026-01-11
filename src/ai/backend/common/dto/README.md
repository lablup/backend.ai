# Shared DTOs (Data Transfer Objects)

This module contains Data Transfer Objects (DTOs) that are shared between Backend.AI components.

## Purpose

DTOs in `ai.backend.common.dto` define the contracts for inter-component communication, including:
- RPC calls between components (Manager ↔ Agent, Manager ↔ Storage, etc.)
- REST API request/response schemas
- Message queue event payloads
- Shared domain models referenced by multiple components

## Organization

DTOs are organized by the target component that exposes them:

```
dto/
├── agent/          # DTOs for Agent component APIs
├── manager/        # DTOs for Manager component APIs
├── storage/        # DTOs for Storage component APIs
└── internal/       # Internal system DTOs (health checks, etc.)
```

## When to Add DTOs Here

**✅ Add to `common/dto/` when:**
- The DTO is used in RPC calls between components
- The DTO is part of a REST API exposed to external clients
- Multiple components need to share the same data structure
- The DTO represents a public API contract
- Changes to the DTO require coordinated updates across components

**❌ Do NOT add to `common/dto/` when:**
- The DTO is used only within a single component
- The DTO is an internal implementation detail
- No other component needs to reference it

For component-internal DTOs, use:
- Manager: `ai.backend.manager.data/{domain}/`
- Agent: `ai.backend.agent.data/` (if needed)

**Note on legacy `{package}/dto/` modules:**
- `ai.backend.manager.dto/` and `ai.backend.storage.dto/` are legacy inter-component DTO modules
- These should be gradually migrated to `common/dto/{component}/`
- For new inter-component DTOs, always use `common/dto/` instead of `{package}/dto/`

## Guidelines

### 1. Use Pydantic Models for External APIs

DTOs exposed through REST APIs or consumed by external clients should use Pydantic models for validation:

```python
from pydantic import BaseModel, Field

class CreateSessionRequest(BaseModel):
    """Request to create a new compute session."""

    image: str = Field(..., description="Container image to use")
    resource_slots: dict[str, str] = Field(..., description="Resource allocation")
    tag: str | None = Field(None, description="Session tag for grouping")
```

### 2. Use Dataclasses for Internal RPC

For internal RPC between Backend.AI components, prefer dataclasses for simplicity:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentHeartbeat:
    """Internal heartbeat message from Agent to Manager."""

    agent_id: str
    timestamp: float
    resource_stats: dict[str, float]
```

### 3. Immutability

DTOs should be immutable whenever possible:
- For Pydantic models: Use `model_config = ConfigDict(frozen=True)`
- For dataclasses: Use `@dataclass(frozen=True)`
- For sequences: Use `tuple` instead of `list`

```python
from pydantic import BaseModel, ConfigDict

class SessionInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str
    mounts: tuple[str, ...]  # Use tuple, not list
```

### 4. Backward Compatibility

**IMPORTANT:** DTOs in this module are public contracts. Changes must maintain backward compatibility or use versioning:

- **Adding fields:** Safe if optional with defaults
- **Removing fields:** Requires deprecation period and coordination
- **Changing field types:** Generally breaking change
- **Renaming fields:** Breaking change, use field aliases for transition

Example of backward-compatible addition:
```python
class SessionRequest(BaseModel):
    image: str
    resource_slots: dict[str, str]
    # New optional field with default - backward compatible
    enable_monitoring: bool = False
```

### 5. Documentation

All DTOs must have:
- Class docstring explaining the purpose
- Field descriptions using Pydantic's `Field()` or inline comments

```python
class DeploymentStatus(BaseModel):
    """Status information for a model deployment.

    This DTO is returned by the Manager's deployment API
    and consumed by the web UI.
    """

    deployment_id: str = Field(..., description="Unique deployment identifier")
    state: str = Field(..., description="Current deployment state")
    replicas: int = Field(..., description="Number of running replicas")
```

## Directory Structure by Component

### agent/
DTOs for Agent component APIs - used by Manager to communicate with Agents.

Examples:
- Container lifecycle requests/responses
- Resource allocation commands
- Health check responses

### manager/
DTOs for Manager component APIs - used by external clients and other components.

Subdirectories:
- `auth/` - Authentication and authorization DTOs
- `notification/` - Notification system DTOs
- `rbac/` - Role-based access control DTOs

Examples:
- Session creation/termination requests
- User management requests
- GraphQL/REST API schemas

### storage/
DTOs for Storage component APIs - used by Manager and other components for storage operations.

Examples:
- Volume creation/deletion requests
- File upload/download operations
- Storage quota management

### internal/
System-internal DTOs not exposed to external clients.

Examples:
- Health check responses
- Internal monitoring data
- Cross-component system events

## Migration Process

### Moving from Legacy `{package}/dto/` to `common/dto/`

**Priority migration:** Legacy inter-component DTOs in `{package}/dto/` should be moved here:

1. **Identify** DTOs used in inter-component communication (RPC, message queues)
2. **Copy** the DTO to the appropriate `common/dto/{component}/` directory
3. **Convert** to Pydantic if not already (recommended for inter-component communication)
4. **Add** backward compatibility imports in legacy location:
   ```python
   # In ai.backend.storage.dto/legacy_module.py
   from ai.backend.common.dto.storage.new_module import NewDTO as LegacyDTO

   __all__ = ["LegacyDTO"]
   ```
5. **Update** imports gradually across components
6. **Document** deprecation in legacy module
7. **Remove** legacy module after all references are updated

### Moving from Component-Internal to Shared

When a component-internal DTO needs to be shared:

1. **Copy** the DTO to the appropriate `common/dto/{component}/` directory
2. **Convert** to Pydantic (recommended for inter-component communication)
3. **Update** imports in the original component
4. **Document** the DTO's purpose and consumers
5. **Coordinate** with teams that will use it
6. **Remove** from component-internal location after transition

### Moving from Shared to Component-Internal

When a shared DTO is no longer used across components:

1. **Verify** no other components reference it (grep, IDE search)
2. **Move** to component's `data/` directory (NOT `dto/`)
3. **Simplify** to dataclass if Pydantic validation is not needed
4. **Update** imports
5. **Remove** from `common/dto/`

## Examples

See existing DTOs for patterns:
- **REST API request:** `manager/request.py`
- **REST API response:** `manager/response.py`
- **RPC request:** `agent/request.py` (if exists)
- **RPC response:** `agent/response.py`
- **Shared types:** `manager/types.py`, `storage/types.py`

## See Also

- [Manager Data README](../../manager/data/README.md) - Component-internal DTOs
- [Storage DTO README](../../storage/dto/README.md) - Component-internal DTOs
