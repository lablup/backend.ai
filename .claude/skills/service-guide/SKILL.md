---
name: service-guide
description: Guide for implementing Backend.AI service layer (create, get, search, update, delete, purge, batch operations, Actions, ActionResults, Processors, ActionProcessor, Service methods)
version: 1.0.0
dependencies:
  - repository-guide
  - test-guide
tags:
  - service-layer
  - actions
  - processors
  - business-logic
---

# Service layer implementation guide

The service layer uses Actions, Processors and service methods.

## Standard operations

Services implement 6 standard operations:

1. **create** - create a new entity
2. **get** - get a single entity
3. **search** - query with filters
4. **update** - update an entity
5. **delete** - delete an entity
6. **purge** - permanently remove an entity

`batch_*` runs atomically in one statement. `bulk_*` handles rows individually with partial failures. See `/repository-guide`.

Method naming has no prefix:

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

Components:

- **Actions** - immutable dataclasses that describe operations
- **ActionResults** - immutable dataclasses that hold results
- **Processors** - orchestration with hooks and metrics
- **Service methods** - business logic
- **Repositories** - data access

## Directory structure

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

- Frozen dataclasses for immutability
- Base classes define `entity_id()` and `operation_type()`
- Concrete actions for each operation (create, get, search, update, delete, purge)
- Corresponding ActionResult types

See `services/storage_namespace/actions/` for the full implementations and `services/storage_namespace/actions/base.py` for the base classes.

## Processors

- `ActionProcessor` wraps service methods
- It provides hooks and metrics integration
- Expose processors via properties
- Initialize with the service protocol

See `services/storage_namespace/processors.py` for the processor package and `services/processors.py` for the base processor classes.

## Service implementation

- Define a Protocol with all operation methods
- Implement the service class, which accepts Actions and returns ActionResults
- Follow: validate → business rules → repository call → return result

Operation patterns:

- `create_{entity}` - validate → check existence → create
- `{entity}` - get → check not found → return
- `search_{entities}` - build scope and filters → `repository.search`
- `update_{entity}` - validate → update → return
- `delete_{entity}` - mark the row as deleted while keeping it
- `purge_{entity}` - permanently remove the entity

### Repository call pattern

The service method calls a single repository method. Avoid combining multiple repository calls in the service layer. When complex composition is needed, consider adding a specialized repository method.

Transaction boundary:

- DB sessions are created and managed at the repository method level
- Service methods do not create transactions directly
- The repository uses `begin_session()` for writes and `begin_readonly_session()` for reads
- Each repository public method defines its own transaction scope

Multi-repository coordination is acceptable when the business logic requires it. For example, creating a domain requires both the domain and user_group repositories. Document the reason when combining multiple repository calls.

See `services/storage_namespace/service.py:38-81` for the single repository call pattern, `services/domain/service.py` for multi-repository coordination, and `repositories/README.md:54-61` for the service and repository integration principles.

## Implementation workflow

### Step 1: Define the operations enum

**File:** `services/{domain}/types.py`

Define a `StrEnum` with the 6 operations: CREATE, GET, SEARCH, UPDATE, DELETE, PURGE. See `services/storage_namespace/types.py`.

### Step 2: Create the base actions

**File:** `services/{domain}/actions/base.py`

Define the base classes with `entity_id()` and `operation_type()`.

### Step 3: Implement the concrete actions

**Files:** `services/{domain}/actions/{operation}.py`

Create one for each operation: create, get, search, update, delete, purge.

### Step 4: Define the service protocol

**File:** `services/{domain}/service.py`

Define the Protocol with all standard operations.

### Step 5: Implement the service

In the same file, initialize the service with the repository, implement all operations, and follow: validate → business rules → repository → return result.

### Step 6: Create the processor package

**File:** `services/{domain}/processors.py`

Create a processor for each operation and expose them via properties.

### Step 7: Write tests

See `/test-guide` for the full testing workflow. Service tests mock the repositories; they do not use a real DB.

### Step 8: Integrate with the API

See `/api-guide` for REST and GraphQL integration.

## Common patterns

| Operation | Key steps | Exception handling |
|---|---|---|
| **create** | validate → check existence → create → return | `{Entity}AlreadyExists` |
| **get** | get → not found check → return | `{Entity}NotFound` |
| **search** | build scope → `repository.search` → return | none |
| **update** | validate → get → update → return | `{Entity}NotFound`, `Invalid{Entity}` |
| **delete** | check existence → delete → return | `{Entity}NotFound` |
| **purge** | check existence → check dependencies → purge → return | `{Entity}HasDependents` |

**Complete examples:** `src/ai/backend/manager/services/storage_namespace/service.py`

## Best practices

### Action design

- Immutable: `@dataclass(frozen=True)`
- Complete: all operation parameters
- Self-describing names

### Service method design

- Single responsibility
- Explicit exceptions that inherit from `BackendAIError`
- Repository coordination only
- Always return an ActionResult
- Single repository call per method
- Transaction boundary managed by the repository

### Processor design

- Thin orchestration
- Use ActionProcessor for hooks
- Property pattern

### Testing

- Mock the repositories; do not use a real DB
- Test the business logic
- Check the repository calls

See `/test-guide`.

## Related documents

- `/repository-guide` - Data access
- `/api-guide` - REST and GraphQL integration
- `/test-guide` - Scenario-first testing
- `src/ai/backend/manager/services/README.md` - Service layer reference

## Examples

- `src/ai/backend/manager/services/storage_namespace/` - Full service
- `src/ai/backend/manager/services/domain/` - Multi-repository coordination
- `src/ai/backend/manager/services/auth/` - Hook integration
