---
name: api-guide
description: Guide for implementing REST and GraphQL APIs (create, get, search, update, delete, purge, scope prefix patterns, admin_ prefix, SearchScope, BaseFilterAdapter, @api_function, Click CLI)
version: 1.0.0
dependencies:
  - service-guide
  - repository-guide
tags:
  - rest-api
  - graphql
  - client-sdk
  - cli
  - api-patterns
---

# API Implementation Guide

Guide for implementing REST and GraphQL APIs with standard operations and scope patterns.

## Standard Operations

APIs implement 6 standard operations:

1. **create** - Create new entity
2. **get** - Retrieve single entity
3. **search** - Query with filters and pagination
4. **update** - Update entity
5. **delete** - Delete entity (soft)
6. **purge** - Permanently remove entity (hard)

**Batch operations:** `batch_update`, `batch_delete`, `batch_purge`

## Scope Prefix Rules

**API layer only** (Service/Repository layers don't use prefix)

### Scoped Operations

Operations within a scope use `{scope}_` prefix:

**REST:**
```
POST   /domains/{domain}/users        → domain_create_user
GET    /domains/{domain}/users/{id}   → domain_user
GET    /domains/{domain}/users         → domain_search_users
PATCH  /domains/{domain}/users/{id}   → domain_update_user
DELETE /domains/{domain}/users/{id}   → domain_delete_user
```

**GraphQL:**
```graphql
mutation domainCreateUser(scope: DomainScope, input: ...)
query domainUser(scope: DomainScope, id: ID)
query domainSearchUsers(scope: DomainScope, filter: ...)
```

### Admin Operations (No Scope)

Operations without scope use `admin_` prefix (superadmin required):

**REST:**
```
POST   /admin/domains        → admin_create_domain
GET    /admin/domains/{id}   → admin_domain
GET    /admin/domains         → admin_search_domains
```

**GraphQL:**
```graphql
mutation adminCreateDomain(input: ...)
query adminDomain(id: ID)
query adminSearchDomains(filter: ...)
```

## REST API Patterns

### Architecture

```
REST Handler → Processor → Service → Repository
```

**Key Files:**
- `src/ai/backend/manager/api/{domain}/handler.py` - Handlers
- `src/ai/backend/manager/api/{domain}/adapter.py` - Filters
- `src/ai/backend/manager/api/adapter.py` - Base adapter

### Processor-Based Service Invocation

**Core principle:**
- REST/GraphQL handlers MUST call service methods through Processors
- Never call service methods directly from handlers
- Processors wrap service methods as Actions and provide cross-cutting concerns (hooks, metrics, monitoring)

**Pattern:**
1. Handler creates Action with operation parameters
2. Handler calls processor's `wait_for_complete()` with Action
3. Processor invokes corresponding service method and returns ActionResult

**ActionProcessor responsibilities:**
- Action-based service method invocation
- Hook execution (pre/post operation)
- Metrics collection and monitoring
- Error handling and logging

**See complete examples:**
- `api/fair_share/handler.py:144` - Handler calling processor
- `services/storage_namespace/processors.py:29-56` - Processor implementation
- `services/processors.py` - ActionProcessor base class

### Scope Pattern

Scope defines access boundaries.

**Repository Scope:**
- `src/ai/backend/manager/repositories/{domain}/types.py`
- Example: `repositories/fair_share/types.py`
  - `DomainFairShareSearchScope`, `ProjectFairShareSearchScope`

**Pattern:**
- Frozen dataclass with scope params
- `to_conditions()` converts to query conditions

**See complete examples:**
- `api/fair_share/handler.py` - Scoped handler implementations

### Scope Parameter Usage

**Scope parameter is needed for:**

1. **search** - Filter multiple items within scope
   ```python
   domain_search_users(scope: DomainScope, filter: ...)
   ```

2. **batch operations** - Process multiple items within scope
   ```python
   domain_batch_update_users(scope: DomainScope, ids: list[ID], ...)
   ```

**Scope parameter is NOT needed for:**

1. **get** - ID uniquely identifies item
   ```python
   user(id: ID)  # ✅ No scope needed
   # domain_user(scope: DomainScope, id: ID)  # ❌ Unnecessary
   ```

2. **update/delete/purge** - ID uniquely identifies item
   ```python
   update_user(id: ID, data: ...)  # ✅ No scope
   delete_user(id: ID)  # ✅ No scope
   ```

3. **create** - Scope info in data
   ```python
   create_user(data: CreateUserData)  # data contains domain_name
   ```

**Note:** Scope prefix in API name (`domain_search_users`) is different from scope parameter (`scope: DomainScope`).

### Filter Pattern

Filters convert API params to QueryCondition.

**Adapter:**
- `api/adapter.py` - BaseFilterAdapter
- `api/fair_share/adapter.py` - Domain adapters

**Pattern:**
- `to_conditions(filters)` → `list[QueryCondition]`
- `to_orders(order_by)` → `list[QueryOrder]`
- Adapter → `BatchQuerier` → Repository

**See complete examples:**
- `api/fair_share/adapter.py` - Filter adapters
- `api/fair_share/handler.py` - Handler implementations with BatchQuerier

### Admin_ Prefix Pattern

Admin operations require superadmin check before processing.

**Pattern:**
- `_check_superadmin(request)` at handler start
- Raise `InsufficientPermission` if not superadmin

**See complete examples:**
- `api/rbac/handler.py` - Admin handler implementations

### Pagination

REST uses offset-based pagination.

```python
class PaginationQuery(BaseModel):
    offset: int = 0
    limit: int = 20

# Response
class SearchResult(BaseModel):
    items: list[Item]
    total_count: int
    offset: int
    limit: int
```

**Client calculates:** `has_next = offset + limit < total_count`

## GraphQL Patterns

### Architecture

```
GraphQL Resolver → check_admin_only (if admin) → Processor → Service → Repository
```

**Key Files:**
- `src/ai/backend/manager/api/gql/{domain}/resolver/` - Resolvers
- `src/ai/backend/manager/api/gql/types.py` - Input types
- `src/ai/backend/manager/api/gql/utils.py` - Utilities

### Type System Rules

**Strawberry Runtime Evaluation:**
- Strawberry types are evaluated at runtime
- NEVER use TYPE_CHECKING for Strawberry types (Connection, Filter, OrderBy, Input, Type)
- ALWAYS import Strawberry types directly at module level
- Only use TYPE_CHECKING for data layer types not used by Strawberry
- If lazy import needed: use strawberry.lazy() or string-based forward references

**Naming Convention:**
- All GraphQL types MUST have `GQL` suffix (DomainGQL, DomainScopeGQL, DomainFilterGQL)
- Distinguishes GraphQL types from data layer types
- Applies to: @strawberry.type, @strawberry.input, @strawberry.enum classes

**Scope vs Filter:**
- Scope: Required context parameters (resource_group, domain_name, project_id)
- Filter: Optional filtering conditions (name contains, status equals, created after)
- NEVER put optional fields in Scope - use Filter instead
- Scope fields must all be required (no default values, no Optional types)

**See examples:**
- `api/gql/domain_v2/types/node.py` - DomainV2GQL with fair_shares/usage_buckets
- `api/gql/fair_share/types/*.py` - Scope and Filter patterns

### Scope Pattern

**Input Types:**
- `api/gql/types.py`
  - `ResourceGroupDomainScope`, `ResourceGroupProjectScope`, `ResourceGroupUserScope`

**Pattern:**
- Strawberry `@input` maps to repository SearchScope
- GraphQL input → Repository scope type conversion

**See complete examples:**
- `api/gql/types.py` - Scope input types
- `api/gql/fair_share/resolver/domain.py` - Resolver implementations

### Admin Check

**Pattern:**
- `check_admin_only(info)` at resolver start
- Raise `InsufficientPermission` if not superadmin

**See complete examples:**
- `api/gql/utils.py` - `check_admin_only()` utility
- `api/gql/*/resolver/*.py` - Admin resolver implementations

### Pagination

GraphQL supports cursor-based (Relay spec).

```python
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None

@strawberry.type
class UserConnection:
    edges: list[UserEdge]
    page_info: PageInfo
    total_count: int
```

**See:** `api/gql/` for cursor pagination examples

## REST vs GraphQL

| Aspect | REST | GraphQL |
|--------|------|---------|
| **Scope** | PathParam/QueryParam | Strawberry input |
| **Admin Check** | `_check_superadmin(request)` | `check_admin_only(info)` |
| **Naming** | `domain_create_user` | `domainCreateUser` |
| **Pagination** | Offset | Offset or Cursor |
| **Response** | Pydantic | Strawberry type |

## Client SDK + CLI Integration

**When implementing REST API, also implement:**

1. ✅ **SDK Function** (`client/func/{domain}.py`)
   - Use `@api_function` decorator
   - Map to REST endpoint

2. ✅ **CLI Command** (`client/cli/admin/{domain}.py`)
   - Click command
   - Calls SDK function

**Integration flow:**
```
CLI → SDK → REST API → Processor → Service → Repository
```

**See examples:**
- `src/ai/backend/client/func/admin.py` - SDK
- `src/ai/backend/client/cli/admin/user.py` - CLI

## Testing

**See:** `/tdd-guide` skill and `tests/CLAUDE.md` for complete testing strategies.

**Test hierarchy:**
```
Repository Tests → Real DB (with_tables)
Service Tests → Mock repositories
API Handler Tests → Mock processors
CLI Tests → Mock HTTP
```

## Implementation Checklist

**When implementing new API:**

1. ✅ **Repository** (`/repository-guide`)
   - Implement standard operations
   - Define SearchScope

2. ✅ **Service** (`/service-guide`)
   - Define Actions/ActionResults
   - Implement service methods
   - Create processors

3. ✅ **REST API**
   - Handler with scope prefix
   - Admin check if needed
   - Filter adapter

4. ✅ **GraphQL** (optional)
   - Input types
   - Resolver with scope prefix
   - Admin check if needed

5. ✅ **Client SDK**
   - Add SDK function
   - `@api_function` decorator

6. ✅ **CLI**
   - Click command
   - Integrate with SDK

7. ✅ **Tests**
   - Repository (real DB)
   - Service (mock repo)
   - Handler (mock processors)
   - CLI (mock HTTP)

## Related Documentation

- **Service Layer**: `/service-guide` - Actions, Processors
- **Repository Layer**: `/repository-guide` - Data access
- **Testing**: `/tdd-guide` - TDD workflow
- **API README**: `src/ai/backend/manager/api/README.md`

## Examples

**REST API:**
- `src/ai/backend/manager/api/fair_share/handler.py`
- `src/ai/backend/manager/api/rbac/handler.py`

**GraphQL:**
- `src/ai/backend/manager/api/gql/fair_share/resolver/domain.py`
- `src/ai/backend/manager/api/gql/types.py`

**Client SDK/CLI:**
- `src/ai/backend/client/func/admin.py`
- `src/ai/backend/client/cli/admin/user.py`

## Summary

**Standard operations:**
- create, get, search, update, delete, purge
- batch_update, batch_delete, batch_purge

**Scope prefix (API only):**
- Scoped: `{scope}_operation` (domain_create_user)
- Admin: `admin_operation` (admin_create_domain)

**Key patterns:**
- Scope → SearchScope → QueryCondition
- Filter → Adapter → QueryCondition
- Admin → check permission first

**Integration:**
- REST API + SDK + CLI (unified stack)
- GraphQL (separate, optional)

**Next steps:**
1. Implement repository (`/repository-guide`)
2. Implement service (`/service-guide`)
3. Implement API handlers
4. Add SDK + CLI
5. Write tests (`/tdd-guide`)
