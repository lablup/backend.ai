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

# Repository development guide

Repositories use base patterns and standard operations.

## Standard operations

Repositories implement 6 standard operations:

1. **create** - create a new entity
2. **get** - get a single entity by id
3. **search** - query with filters and pagination
4. **update** - update an existing entity
5. **delete** - marks the row as deleted while keeping it
6. **purge** - permanently removes the row

Target semantics:

- **Single** (`create`, `get`, `update`, `delete`, `purge`): one row by primary key.
- **Batch** (`batch_*`): many rows in one SQL statement, **atomic** (all or nothing). It returns only the affected-row count.
- **Bulk** (`bulk_*`): rows processed individually, with **partial failures allowed**. It returns successes and errors.

Method naming has no prefix:

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

## Base utilities

The base utilities live in `src/ai/backend/manager/repositories/base/`. All repositories use them for standard operations.

### SearchScope

SearchScope provides multi-tenant access control for queries.

Implementations live in `repositories/{domain}/types.py`. See `repositories/fair_share/types.py` (`DomainFairShareSearchScope`) and `repositories/group/types.py` (`GroupSearchScope`).

Pattern:

- A frozen dataclass with scope parameters
- `to_conditions()` converts it to query conditions

### Base utility classes

- `Creator[TRow]` - create operations
- `Querier[TRow]` - single entity retrieval (get)
- `BatchQuerier[TRow]` - search with filters and pagination
- `Updater[TRow]` - update with the OptionalState pattern
- `Purger[TRow]` - purge operations
- `BatchUpdater[TRow]`, `BatchPurger[TRow]`: atomic multi-row in a single statement
- `BulkCreator[TRow]`, `BulkUpserter[TRow]`: per-row with partial failures (`execute_bulk_*_partial`)

See `repositories/base/` for the source and `repositories/fair_share/repository.py` for usage.

## DB ops wrapper in `ops/`

`ops/provider.py` wraps `ExtendedAsyncSAEngine` and exposes a spec-only operations surface. The db_sources are moving to this wrapper. New or modified db_sources use `DBOpsProvider` rather than holding the engine and calling `session.execute` directly. Existing db_sources are migrated gradually when touched.

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

- `read_ops()` and `write_ops()` both open a READ COMMITTED session. The raw engine and session are never exposed.
- ops methods accept only spec types, never raw `Select/Insert/Update/Delete`.

### Reads with scope (RBAC)

```python
async with self._ops.read_ops() as r:
    # default: scoped query
    result = await r.batch_query_with_scopes(sa.select(FooRow), querier, scopes)
    # superadmin or internal only: bypasses scope filtering
    result = await r.batch_query_in_global(sa.select(FooRow), querier)
```

Use `batch_query_in_global` only for superadmin-only endpoints or internal system operations; it bypasses RBAC scope filtering. Empty `scopes` for the scoped variant raises `EmptySearchScopeError` (400).

### Single-table specs and multi-table coordination

Each spec owns exactly one table. Do not build child-table rows inside a creator or updater spec. For a parent with dependent children, the repository coordinates the sequence procedurally, without a tree object:

```python
async with self._ops.write_ops() as w:
    parent = (await w.create(Creator(spec=parent_spec))).row
    dep = ChildDependency(parent_id=parent.id)          # build dependency from the result
    children = (await w.bulk_create_dependent(child_specs, dep)).rows
```

- `DependentCreatorSpec[TDependency, TRow].build_row(dependency)` builds one row from a dependency resolved at execution time, for example the generated id of the parent.
- `create_dependent` (single) and `bulk_create_dependent` (multiple) execute them.
- An update that replaces child rows is an update of the parent, a purge of the old children, and `bulk_create_dependent` for the new children, all inside one `write_ops()` block.

## Implementation pattern

- Initialize the base utilities in `__init__`
- Implement the 6 standard operations with the base utilities
- Use `begin_session()` for writes and `begin_readonly_session()` for reads
- Pass the scope to the base utilities
- Add batch operations when needed

See `repositories/fair_share/repository.py` for a full repository, `repositories/group/repository.py` for scope usage, and `repositories/domain/repository.py` for standard operations.

## DB source and cache source architecture

Repositories are moving to delegate data access to the DB Source pattern. The repository coordinates the DB Source and, when present, the Cache Source.

- The DB Source handles the actual database queries and transactions.
- The Cache Source handles cache invalidation and retrieval.

Directory structure:

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

Pattern:

- The repository imports and uses the `db_source` module
- Repository public methods delegate to DB Source methods
- Transactions are managed at the DB Source level, with `begin_session()` or `begin_readonly_session()`
- The Cache Source handles cache invalidation and retrieval when present

Responsibilities:

- **Repository** - public API, coordination between sources, business logic orchestration
- **DB Source** - database queries, transaction management, ORM operations
- **Cache Source** - cache reads and writes, invalidation strategies

See `repositories/fair_share/repository.py:39` for DB Source usage, `repositories/fair_share/db_source/db_source.py` for the implementation, `repositories/scheduler/cache_source/cache_source.py` for a Cache Source, and `repositories/README.md:78` for cache management.

Not all repositories have migrated to this pattern. New repositories use it and existing repositories are migrated gradually when modified.

## Implementation steps

### 1. Define types

**File:** `repositories/{domain}/types.py`

Define the SearchScope dataclass with a `to_conditions()` method. See `repositories/fair_share/types.py` for multiple scope types and `repositories/group/types.py` for a scope with conditions.

### 2. Implement the repository

**File:** `repositories/{domain}/repository.py`

1. Initialize the base utilities in `__init__`
2. Implement the 6 standard operations
3. Add batch operations when needed
4. Add domain-specific methods

### 3. Write tests

**File:** `tests/unit/manager/repositories/{domain}/test_{operation}.py`

- Use the `with_tables` fixture with a real DB
- Test all standard operations
- Test scope filtering
- Test error cases

See `/test-guide` for the testing workflow.

## Transaction management

- Read operations use `begin_readonly_session()`
- Write operations use `begin_session()`
- Pass `db_sess` to the base utilities

See `repositories/fair_share/repository.py`.

## Query optimization

- Select only the needed columns
- Filter by scope at the DB level
- Add indexes for frequently filtered columns
- Use batch operations for multiple entities
- Avoid N+1 queries

See `repositories/base/` for optimization utilities.

## Scope usage

- Pass the scope to the base utilities (`query()`, `search()`, `purge()`)
- Scope `to_conditions()` converts it to query filters
- Domain scope becomes a `domain_name` filter
- Project scope becomes a `project_id` filter
- User scope becomes a `user_uuid` filter

See `repositories/fair_share/repository.py`.

## Type safety

Use domain types:

- `FairShareId` instead of `str`
- `DomainName` instead of `str`
- Frozen dataclasses for immutability
- Comprehensive type hints

## Error handling

- Define domain exceptions inheriting from `BackendAIError`
- Raise specific exceptions, for example `EntityNotFound` and `EntityAlreadyExists`
- Provide clear error messages

See `repositories/fair_share/repository.py`.

## Example repositories

- `src/ai/backend/manager/repositories/fair_share/` - Complete implementation
- `src/ai/backend/manager/repositories/group/` - Scope usage
- `src/ai/backend/manager/repositories/domain/` - Standard operations

## Related documents

- `/service-guide` - Service methods that use repositories
- `/api-guide` - API handlers that call services
- `/test-guide` - Scenario-first testing with repositories
- `repositories/README.md` - Architecture overview

## Troubleshooting

**SearchScope does not filter:**

- Verify that `to_conditions()` returns the correct conditions
- Check the scope passed to the base utility
- Verify that the column names match the table

**FK constraint violations:**

- Create parent entities first in tests
- Use the `with_tables` fixture
- Check the cascade settings

**Type errors:**

- Use the correct generic type, for example `Querier[YourRow]`
- Match the primary key column type with the table definition
- Use domain types consistently

**Performance issues:**

- Add indexes for filtered columns
- Use `begin_readonly_session()` for reads
- Use batch operations for multiple entities
- Profile the queries with EXPLAIN
