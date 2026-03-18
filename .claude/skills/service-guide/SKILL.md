---
name: service-guide
description: Guide for implementing Backend.AI service layer (create, get, search, update, delete, purge, batch operations, Actions, ActionResults, Processors, ActionProcessor, Service methods)
version: 1.0.0
dependencies:
  - repository-guide
  - tdd-guide
tags:
  - service-layer
  - actions
  - processors
  - business-logic
---

# Service Layer Implementation Guide

Guide for implementing Backend.AI service layer with Actions, Processors, and Service methods.

## Standard Operations

Services implement 6 standard operations:

1. **create** - Create new entity
2. **get** - Retrieve single entity
3. **search** - Query with filters
4. **update** - Update entity
5. **delete** - Delete entity
6. **purge** - Permanently remove entity

**Batch operations:** `batch_update`, `batch_delete`, `batch_purge`

**Method naming (no prefix):**
```python
await service.create_user(action: CreateUserAction)
await service.user(action: GetUserAction)
await service.search_users(action: SearchUsersAction)
await service.update_user(action: UpdateUserAction)
await service.delete_user(action: DeleteUserAction)
await service.purge_user(action: PurgeUserAction)
```

## Architecture

```
API Handler → Processor → Service → Repository
```

**Components:**
- **Actions**: Immutable dataclasses (operations)
- **ActionResults**: Immutable dataclasses (results)
- **Processors**: Orchestrate with hooks and metrics
- **Service Methods**: Business logic
- **Repositories**: Data access

## Directory Structure

```
services/{domain}/
├── types.py              # Operation enums
├── service.py            # Service protocol + implementation
├── processors.py         # Processor package
└── actions/
    ├── base.py          # Base action classes
    ├── create.py        # Create action
    ├── get.py           # Get action
    ├── search.py        # Search action
    ├── update.py        # Update action
    ├── delete.py        # Delete action
    └── purge.py         # Purge action
```

**Example:** `src/ai/backend/manager/services/storage_namespace/`

## Actions and ActionResults

**Pattern:**
- Frozen dataclasses for immutability
- Base classes define `entity_id()` and `operation_type()`
- Concrete actions for each operation (create, get, search, update, delete, purge)
- Corresponding ActionResult types

**See complete examples:**
- `services/storage_namespace/actions/` - Full action implementations
- `services/storage_namespace/actions/base.py` - Base classes

## Processors

**Pattern:**
- `ActionProcessor` wraps service methods
- Provides hooks and metrics integration
- Expose processors via properties
- Initialize with service protocol

**See complete examples:**
- `services/storage_namespace/processors.py` - Processor package
- `services/processors.py` - Base processor classes

## Service Implementation

**Pattern:**
- Define Protocol with all operation methods
- Implement service class accepting Actions, returning ActionResults
- Follow: validate → business rules → repository call → return result

**Operation patterns:**
- `create_{entity}`: Validate → check existence → create
- `{entity}`: Fetch → check not found → return
- `search_{entities}`: Build scope/filters → repository.search
- `update_{entity}`: Validate → update → return
- `delete_{entity}`: Soft delete (status change)
- `purge_{entity}`: Hard delete

### Repository Call Pattern

**Core principle (preferred):**
- Service method SHOULD call a single repository method
- Avoid combining multiple repository calls in service layer
- If complex composition is needed, consider adding specialized repository method

**Transaction boundary:**
- DB sessions are created and managed at repository method level
- Service methods do NOT create transactions directly
- Repository uses `begin_session()` (write) or `begin_readonly_session()` (read)
- Each repository public method defines its own transaction scope

**Exception cases:**
- Multi-repository coordination is acceptable when business logic requires
- Example: Creating domain requires both domain and user_group repositories
- Document the reason when combining multiple repository calls

**See complete examples:**
- `services/storage_namespace/service.py:38-81` - Single repository call pattern
- `services/domain/service.py` - Multi-repository coordination (exceptional case)
- `repositories/README.md:54-61` - Service-Repository integration principles


## Implementation Workflow

### Step 1: Define Operations Enum

**File:** `services/{domain}/types.py`

Define `StrEnum` with 6 operations: CREATE, GET, SEARCH, UPDATE, DELETE, PURGE

**See:** `services/storage_namespace/types.py`

### Step 2: Create Base Actions

**File:** `services/{domain}/actions/base.py`

Define base classes with `entity_id()` and `operation_type()`

### Step 3: Implement Concrete Actions

**Files:** `services/{domain}/actions/{operation}.py`

For each operation: create, get, search, update, delete, purge

### Step 4: Define Service Protocol

**File:** `services/{domain}/service.py`

Protocol with all standard operations

### Step 5: Implement Service

**Same file**

- Initialize with repository
- Implement all operations
- Follow: validate → business rules → repository → return result

### Step 6: Create Processor Package

**File:** `services/{domain}/processors.py`

- Processor for each operation
- Expose via properties

### Step 7: Write Tests

**See:** `/tdd-guide` for complete testing workflow

**Critical:** Service tests MUST mock repositories (no real DB)

### Step 8: Integrate with API

**See:** `/api-guide` for REST and GraphQL integration

## Common Patterns

| Operation | Key Steps | Exception Handling |
|-----------|-----------|-------------------|
| **create** | validate → check existence → create → return | `{Entity}AlreadyExists` |
| **get** | fetch → not found check → return | `{Entity}NotFound` |
| **search** | build scope → repository.search → return | - |
| **update** | validate → fetch → update → return | `{Entity}NotFound`, `Invalid{Entity}` |
| **delete** | check exists → delete → return | `{Entity}NotFound` |
| **purge** | check exists → check dependencies → purge → return | `{Entity}HasDependents` |

**Complete examples:** `src/ai/backend/manager/services/storage_namespace/service.py`

## Best Practices

### Action Design
- Immutable: `@dataclass(frozen=True)`
- Complete: All operation params
- Self-describing names

### Service Method Design
- Single responsibility
- Explicit exceptions (inherit BackendAIError)
- Repository coordination only
- Always return ActionResult
- Single repository call per method (preferred pattern)
- Transaction boundary managed by repository

### Processor Design
- Thin orchestration
- Use ActionProcessor for hooks
- Property pattern

### Testing
- Mock repositories (never real DB)
- Test business logic
- Verify repository calls

**See:** `/tdd-guide` skill

## Related Documentation

- **Repository Layer**: `/repository-guide` - Data access
- **API Integration**: `/api-guide` - REST/GraphQL
- **Testing**: `/tdd-guide` - TDD workflow
- **Service README**: `src/ai/backend/manager/services/README.md`

## Examples

**Complete implementations:**
- `src/ai/backend/manager/services/storage_namespace/` - Full service
- `src/ai/backend/manager/services/domain/` - Multi-repository
- `src/ai/backend/manager/services/auth/` - Hook integration

## Summary

**Standard operations:**
- create, get, search, update, delete, purge
- batch_update, batch_delete, batch_purge

**Components:**
- Actions/ActionResults (immutable)
- Processors (orchestration)
- Service methods (business logic)

**Testing:** Mock repositories (no real DB)

**Next steps:**
1. Study example services
2. Define actions and operations
3. Implement service methods
4. Create processors
5. Write tests (`/tdd-guide`)
6. Integrate with API (`/api-guide`)
