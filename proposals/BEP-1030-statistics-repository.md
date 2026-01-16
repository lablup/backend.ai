---
Author: Bokeum Kim (bkkim@lablup.com)
Status: Draft
Created: 2025-01-16
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# Statistics Repository Layer

## Motivation

### Problem: GraphQL DataLoader Discovery Failure

GraphQL queries requesting the `inference_metrics` field fail with the following error:

```
Type 'KernelStatistics' not found in gql_legacy submodules
```

**Steps to Reproduce:**

Execute the following query via Admin GraphQL API:

```graphql
query {
  compute_session_list {
    items {
      inference_metrics
    }
  }
}
```

**Error Response:**

```json
{
  "message": "Type 'KernelStatistics' not found in gql_legacy submodules",
  "locations": [{"line": 1, "column": 450}],
  "path": ["compute_session_list", "items", 0, "inference_metrics"]
}
```

### Root Cause Analysis

`DataLoaderManager._build_gql_type_cache()` (`api/gql_legacy/base.py:247-268`) only scans Python files within the `gql_legacy` directory and caches types defined in each module's `__all__`.

However, `KernelStatistics` and `EndpointStatistics` are defined in:
- `models/kernel/row.py` (line 1088-1115)
- `models/endpoint/row.py` (line 1463-1490)

Since these classes are **not in the `gql_legacy` directory**, they are not included in the type cache.

**Call flow:**

```
ComputeSession.resolve_inference_metrics()
  → dataloader_manager.get_loader(ctx, "KernelStatistics.inference_metrics_by_kernel")
    → load_attr("KernelStatistics")
      → type_cache["KernelStatistics"]  # KeyError!
```

### Architectural Issues

Beyond the immediate bug, the current design has several structural problems:

1. **Violation of separation of concerns**: ORM model files should focus on database schema definitions, not external data source access (Valkey clients)
2. **Inconsistent architecture**: Other data access patterns in the codebase use the Repository pattern with dedicated `*Repository` and `*StatefulSource` classes
3. **Tight coupling**: Statistics logic is tightly coupled with GraphQL context (`GraphQueryContext`), making it harder to reuse in non-GraphQL contexts
4. **Testing difficulty**: Hard to unit test statistics logic independently from ORM models

## Current Design

```python
# models/kernel/row.py
class KernelStatistics:
    @classmethod
    async def batch_load_by_kernel_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await valkey_stat_client.get_session_statistics_batch(session_ids_str)

    @classmethod
    async def batch_load_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        return await cls.batch_load_by_kernel_impl(ctx.valkey_stat, session_ids)

# models/endpoint/row.py
class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint_impl(
        cls,
        valkey_stat_client: ValkeyStatClient,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Optional[Mapping[str, Any]]]:
        endpoint_id_strs = [str(endpoint_id) for endpoint_id in endpoint_ids]
        return await valkey_stat_client.get_inference_app_statistics_batch(endpoint_id_strs)
```

These classes are used in:
- `DeploymentRepository` for fetching deployment metrics
- `ScheduleRepository` for auto-scaling decisions
- GraphQL dataloaders for resolving statistics fields

## Proposed Design

### Layer Structure

```
repositories/statistics/
├── __init__.py
├── repositories.py          # StatisticsRepositories factory
├── repository.py            # StatisticsRepository (public API)
└── stateful_source/
    ├── __init__.py
    └── stateful_source.py   # StatisticsStatefulSource (Valkey access)
```

### StatisticsStatefulSource

Handles direct Valkey client interactions:

```python
class StatisticsStatefulSource:
    _valkey_stat: ValkeyStatClient
    _valkey_live: ValkeyLiveClient

    def __init__(
        self,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
    ) -> None:
        self._valkey_stat = valkey_stat
        self._valkey_live = valkey_live

    async def read_kernel_statistics_batch(
        self,
        session_ids_or_kernel_ids: Sequence[SessionId | KernelId],
    ) -> Sequence[Mapping[str, Any] | None]:
        ids_str = [str(id_) for id_ in session_ids_or_kernel_ids]
        return await self._valkey_stat.get_session_statistics_batch(ids_str)

    async def read_inference_metrics_batch(
        self,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        session_ids_str = [str(sess_id) for sess_id in session_ids]
        return await self._valkey_live.get_session_statistics_batch(session_ids_str)

    async def read_endpoint_statistics_batch(
        self,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        endpoint_ids_str = [str(eid) for eid in endpoint_ids]
        return await self._valkey_stat.get_inference_app_statistics_batch(endpoint_ids_str)

    async def read_replica_statistics_batch(
        self,
        endpoint_replica_pairs: Sequence[tuple[UUID, UUID]],
    ) -> Sequence[Mapping[str, Any] | None]:
        pairs_str = [(str(eid), str(rid)) for eid, rid in endpoint_replica_pairs]
        return await self._valkey_stat.get_inference_replica_statistics_batch(pairs_str)
```

### StatisticsRepository

Public API for statistics access:

```python
class StatisticsRepository:
    _stateful_source: StatisticsStatefulSource

    def __init__(
        self,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
    ) -> None:
        self._stateful_source = StatisticsStatefulSource(
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
        )

    async def get_kernel_statistics_batch(
        self,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await self._stateful_source.read_kernel_statistics_batch(session_ids)

    async def get_inference_metrics_batch(
        self,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await self._stateful_source.read_inference_metrics_batch(session_ids)

    async def get_endpoint_statistics_batch(
        self,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await self._stateful_source.read_endpoint_statistics_batch(endpoint_ids)

    async def get_replica_statistics_batch(
        self,
        endpoint_replica_ids: Sequence[tuple[UUID, UUID]],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await self._stateful_source.read_replica_statistics_batch(endpoint_replica_ids)
```

### GraphQL Integration

New dataloader helpers in `api/gql_legacy/statistics.py`:

```python
class KernelStatistics:
    @classmethod
    async def batch_load_by_kernel(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await ctx.statistics_repository.get_kernel_statistics_batch(session_ids)

class EndpointStatistics:
    @classmethod
    async def batch_load_by_endpoint(
        cls,
        ctx: GraphQueryContext,
        endpoint_ids: Sequence[UUID],
    ) -> Sequence[Mapping[str, Any] | None]:
        return await ctx.statistics_repository.get_endpoint_statistics_batch(endpoint_ids)
```

### GraphQueryContext Update

Add `statistics_repository` to GraphQL context:

```python
@dataclass
class GraphQueryContext:
    # ... existing fields ...
    statistics_repository: StatisticsRepository
```

## Migration / Compatibility

### Backward Compatibility

- This is an internal refactoring with no public API changes
- GraphQL schema and responses remain unchanged
- Existing callers (`DeploymentRepository`, `ScheduleRepository`) are updated to use the new pattern

### Breaking Changes

- `KernelStatistics` removed from `models/kernel/__init__.py`
- `EndpointStatistics` removed from `models/endpoint/__init__.py`
- Internal callers must use `StatisticsStatefulSource` or `StatisticsRepository`

### Migration Steps

1. Remove old `KernelStatistics` and `EndpointStatistics` from model files
2. Update `DeploymentRepository` and `ScheduleRepository` to use `StatisticsStatefulSource`
3. Add `statistics_repository` to `GraphQueryContext`
4. Update GraphQL dataloader references to use new helper classes


## References

- [Repository Pattern in Backend.AI](../src/ai/backend/manager/repositories/README.md)
- Existing repository implementations: `DeploymentRepository`, `ScheduleRepository`, `UserRepository`
