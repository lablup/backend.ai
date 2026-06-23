---
name: repository-guide
description: Guide for implementing Backend.AI repository patterns (create, get, search, update, delete, purge, batch operations, Querier, BatchQuerier, Creator, Updater, Purger, SearchScope, with_tables)
invoke_method: automatic
auto_execute: false
enabled: true
tags:
  - repository
  - data-access
  - querier
  - search-scope
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

**Target semantics:**
- **Single** (`create`/`get`/`update`/`delete`/`purge`) — one row by PK.
- **Batch** (`batch_*`) — many rows in one SQL statement, **atomic** (all-or-nothing); returns only the affected-row count.
- **Bulk** (`bulk_*`) — rows processed individually, **partial failures allowed** (returns successes + errors).

**Method naming (no prefix):**
```python
await repository.create(data)
await repository.get(id, scope=None)
await repository.search(scope, filters, pagination)
await repository.update(id, data)
await repository.delete(id)
await repository.purge(id)
await repository.batch_update(ids, data)   # atomic
await repository.batch_delete(ids)
await repository.batch_purge(ids)
await repository.bulk_create(specs)         # partial failures allowed
await repository.bulk_upsert(specs)
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
- `BatchUpdater[TRow]`, `BatchPurger[TRow]` - atomic multi-row (single statement)
- `BulkCreator[TRow]`, `BulkUpserter[TRow]` - per-row with partial failures (`execute_bulk_*_partial`)

**See implementations:**
- `repositories/base/` - Base utility source code
- `repositories/fair_share/repository.py` - Usage examples

## DB Ops Wrapper (`ops/`) — Preferred for new code

`ops/provider.py` wraps `ExtendedAsyncSAEngine` and exposes a spec-only operations
surface. **Migration direction:** db_sources are moving to this wrapper. New or modified
db_sources SHOULD use `DBOpsProvider` rather than holding the engine and calling
`session.execute` directly. Existing db_sources are migrated gradually when touched.

### Entry points

```python
class FooDBSource:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._ops = DBOpsProvider(db)

    async def foo(self, foo_id: FooID) -> FooData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=FooRow, pk_value=foo_id))
            if result is None:
                raise FooNotFound()
            return result.row.to_data()

    async def create(self, spec: FooCreatorSpec) -> FooData:
        async with self._ops.write_ops() as w:
            result = await w.create(Creator(spec=spec))
            return result.row.to_data()
```

- `read_ops()` / `write_ops()` both open a READ COMMITTED session; the raw engine/
  session is never exposed.
- ops methods accept only spec types — never raw `Select/Insert/Update/Delete`.

### Reads with scope (RBAC)

```python
async with self._ops.read_ops() as r:
    # default — scoped query:
    result = await r.batch_query_with_scopes(sa.select(FooRow), querier, scopes)
    # superadmin / internal only — bypasses scope filtering:
    result = await r.batch_query_in_global(sa.select(FooRow), querier)
```

Use `batch_query_in_global` only for superadmin-only endpoints or internal system
operations; it bypasses RBAC scope filtering. Empty `scopes` for the scoped variant
raises `EmptySearchScopeError` (400).

### Single-table specs + multi-table coordination

Each spec owns exactly one table — never build child-table rows inside a creator/
updater spec. For a parent + dependent children, the repository coordinates the
sequence procedurally (no tree object):

```python
async with self._ops.write_ops() as w:
    parent = (await w.create(Creator(spec=parent_spec))).row
    dep = ChildDependency(parent_id=parent.id)          # build dependency from the result
    children = (await w.bulk_create_dependent(child_specs, dep)).rows
```

- `DependentCreatorSpec[TDependency, TRow].build_row(dependency)` builds one row from a
  dependency resolved at execution time (e.g. the parent's generated id).
- `create_dependent` (single) / `bulk_create_dependent` (multiple) execute them.
- An update that must replace child rows = update parent + purge old children +
  `bulk_create_dependent` new children, all inside one `write_ops()` block.

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

## DB Source and Cache Source Architecture

**Architecture principle:**
- Repositories are transitioning to delegate data access to DB Source pattern
- Repository acts as coordinator between DB Source and Cache Source (if present)
- Actual database queries and transactions are handled by DB Source
- Cache operations are handled by Cache Source (optional)

**Directory structure:**
```
repositories/{domain}/
├── repository.py        # Public interface, source delegation
├── db_source/
│   ├── __init__.py
│   └── db_source.py     # DB operations implementation
└── cache_source/        # (Optional)
    ├── __init__.py
    └── cache_source.py  # Cache operations implementation
```

**Pattern:**
- Repository imports and uses `db_source` module
- Repository public methods delegate to DB Source methods
- Transactions are managed at DB Source level (using `begin_session()` or `begin_readonly_session()`)
- Cache Source handles cache invalidation and retrieval (when present)

**Responsibilities:**
- **Repository**: Public API, coordination between sources, business logic orchestration
- **DB Source**: Database queries, transaction management, ORM operations
- **Cache Source**: Cache reads/writes, invalidation strategies

**See complete examples:**
- `repositories/fair_share/repository.py:39` - DB Source import and usage
- `repositories/fair_share/db_source/db_source.py` - DB Source implementation
- `repositories/scheduler/cache_source/cache_source.py` - Cache Source example
- `repositories/README.md:78` - Cache management reference

**Migration status:**
- Not all repositories have migrated to this pattern yet
- New repositories SHOULD use this pattern
- Existing repositories can be migrated gradually when modified

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

**See:** `/test-guide` skill for testing workflow

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
- **Testing**: `/test-guide` - Scenario-first testing with repositories
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
4. Write tests with `/test-guide`
5. Integrate with service layer (`/service-guide`)
