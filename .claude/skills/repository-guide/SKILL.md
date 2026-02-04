---
name: repository-guide
description: Guide for implementing Backend.AI repository patterns (create, get, search, update, delete, purge, batch operations, Querier, BatchQuerier, Creator, Updater, Purger, SearchScope, with_tables)
invoke_method: automatic
auto_execute: false
enabled: true
---

# Repository Development Guide

Guide for implementing Backend.AI repositories using base patterns and standard operations.

## Standard Operations

Repositories implement 6 standard operations:

1. **create** - Create new entity
2. **get** - Retrieve single entity by ID
3. **search** - Query with filters and pagination
4. **update** - Update existing entity
5. **delete** - Soft delete (status change)
6. **purge** - Hard delete (permanent removal)

**Batch operations:**
- `batch_update` - Update multiple entities
- `batch_delete` - Soft delete multiple entities
- `batch_purge` - Hard delete multiple entities

**Method naming (no prefix):**
```python
await repository.create(data)
await repository.get(id, scope=None)
await repository.search(scope, filters, pagination)
await repository.update(id, data)
await repository.delete(id)
await repository.purge(id)
await repository.batch_update(ids, data)
await repository.batch_delete(ids)
await repository.batch_purge(ids)
```

## Base Utilities

**Located in:** `src/ai/backend/manager/repositories/base/`

All repositories use these base utilities for standard operations:

### SearchScope
Multi-tenant access control for queries.

**Implementations:** `repositories/{domain}/types.py`
- Example: `repositories/fair_share/types.py` - `DomainFairShareSearchScope`
- Example: `repositories/group/types.py` - `GroupSearchScope`

**Pattern:**
- Frozen dataclass with scope parameters
- `to_conditions()` method converts to query conditions

### Base Utility Classes

**Available utilities:**
- `Creator[TRow]` - Create operations
- `Querier[TRow]` - Single entity retrieval (get)
- `BatchQuerier[TRow]` - Search with filters and pagination
- `Updater[TRow]` - Update with OptionalState pattern
- `Purger[TRow]` - Hard delete operations
- `BatchUpdater[TRow]`, `BatchPurger[TRow]` - Batch operations

**See implementations:**
- `repositories/base/` - Base utility source code
- `repositories/fair_share/repository.py` - Usage examples

## Implementation Pattern

**Pattern:**
- Initialize base utilities in `__init__`
- Implement 6 standard operations using base utilities
- Use `begin_session()` for writes, `begin_readonly_session()` for reads
- Pass scope to base utilities
- Add batch operations if needed

**See complete implementation:**
- `repositories/fair_share/repository.py` - Full repository example
- `repositories/group/repository.py` - Scope usage patterns
- `repositories/domain/repository.py` - Standard operations

## Implementation Steps

### 1. Define Types

**File:** `repositories/{domain}/types.py`

Define SearchScope dataclass with `to_conditions()` method.

**See examples:**
- `repositories/fair_share/types.py` - Multiple scope types
- `repositories/group/types.py` - Scope with conditions

### 2. Implement Repository

**File:** `repositories/{domain}/repository.py`

1. Initialize base utilities in `__init__`
2. Implement standard 6 operations
3. Add batch operations if needed
4. Add domain-specific methods

### 3. Write Tests

**File:** `tests/unit/manager/repositories/{domain}/test_{operation}.py`

- Use `with_tables` fixture for real DB
- Test all standard operations
- Test scope filtering
- Test error cases

**See:** `/tdd-guide` skill for testing workflow

## Transaction Management

**Pattern:**
- Read operations: `begin_readonly_session()`
- Write operations: `begin_session()`
- Pass `db_sess` to base utilities

**See examples:** `repositories/fair_share/repository.py`

## Query Optimization

**Tips:**
- Select only needed columns
- Use scope filtering at DB level
- Add indexes for frequently filtered columns
- Use batch operations for multiple entities
- Avoid N+1 queries

**See:** `repositories/base/` for optimization utilities

## Scope Usage

**Pattern:**
- Pass scope to base utilities (`query()`, `search()`, `purge()`)
- Scope `to_conditions()` converts to query filters
- Domain scope → domain_name filter
- Project scope → project_id filter
- User scope → user_uuid filter

**See examples:** `repositories/fair_share/repository.py`

## Type Safety

**Use domain types:**
- `FairShareId` instead of `str`
- `DomainName` instead of `str`
- Frozen dataclasses for immutability
- Comprehensive type hints

## Error Handling

**Pattern:**
- Define domain exceptions inheriting from `BackendAIError`
- Raise specific exceptions (e.g., `EntityNotFound`, `EntityAlreadyExists`)
- Provide clear error messages

**See examples:** `repositories/fair_share/repository.py`

## Example Repositories

**Study these implementations:**
- `src/ai/backend/manager/repositories/fair_share/` - Complete implementation
- `src/ai/backend/manager/repositories/group/` - Scope usage
- `src/ai/backend/manager/repositories/domain/` - Standard operations

## Cross-References

- **Service Layer**: `/service-guide` - Service methods using repositories
- **API Layer**: `/api-guide` - API handlers calling services
- **Testing**: `/tdd-guide` - TDD workflow with repositories
- **Base README**: `repositories/README.md` - Architecture overview

## Troubleshooting

**SearchScope not filtering:**
- Verify `to_conditions()` returns correct conditions
- Check scope passed to base utility
- Verify column names match table

**FK constraint violations:**
- Create parent entities first in tests
- Use `with_tables` fixture
- Check cascade settings

**Type errors:**
- Use correct generic type: `Querier[YourRow]`
- Match PK column type with table definition
- Use domain types consistently

**Performance issues:**
- Add indexes for filtered columns
- Use `begin_readonly_session()` for reads
- Batch operations for multiple entities
- Profile queries with EXPLAIN

## Summary

**Standard operations:**
- create, get, search, update, delete, purge
- batch_update, batch_delete, batch_purge

**Base utilities:**
- Creator, Querier, BatchQuerier, Updater, Purger
- SearchScope for multi-tenant filtering

**Key principles:**
- Public methods use standard names (no prefix)
- Base utilities handle DB operations
- Scope passed for access control
- Transaction management via session context
- Type safety with domain types

**Next steps:**
1. Study example repositories
2. Define types and scope
3. Implement standard operations
4. Write tests with `/tdd-guide`
5. Integrate with service layer (`/service-guide`)
