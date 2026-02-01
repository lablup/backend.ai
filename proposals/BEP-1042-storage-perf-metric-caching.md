---
Author: hyeokjin (hyeokjin@lablup.com)
Status: Draft
Created: 2026-02-01
Created-Version: 25.12.0
Target-Version: 25.12.0
Implemented-Version:
---

# Storage Performance Metric Caching and Observability

## Related Issues

- JIRA: BA-4012 (Epic)
  - BA-4013: Redis cache layer
  - BA-4014: Background refresh + observability
  - BA-4015: Prometheus metrics exposition
  - BA-4016: API modification

## Motivation

Currently, the `/volume/performance-metric` API directly calls external storage backend APIs (NetApp, VAST, PureStorage, GPFS, etc.) on every request. This causes the following problems:

1. **Poor user experience**: When external APIs are slow or unstable, API responses are delayed or fail, resulting in poor user experience
2. **External system latency propagation**: Our API calls are delayed whenever external systems are slow
3. **Lack of observability**: Difficult to monitor storage systems
4. **No history**: Only current values can be queried without time-series data

## Current Design

Current `get_performance_metric` API flow:

```
Client Request
    ↓
API Handler (manager.py:580-603)
    ↓
volume.get_performance_metric()  # Direct external API call
    ↓
Response
```

Each volume implementation directly calls external APIs:
- PureStorage: `purity_client.get_nfs_metric()`
- VAST: `api_client.get_cluster_info()`
- NetApp: `netapp_client.get_volume_by_id()`

## Proposed Design

### Architecture Overview

Use only Redis cache without in-memory cache. When cache is missing or Redis fails, call external API directly.

```
┌─────────────────────────────────────────────────────────────┐
│                VolumeStatsObserver                           │
│  (Periodic background task - 10 second interval)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Volume 1  │    │   Volume 2  │    │   Volume N  │     │
│  │ get_perf_*  │    │ get_perf_*  │    │ get_perf_*  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Redis Cache (TTL: 30s)                  │   │
│  │         storage:perf_metric:{volume_name}           │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ├──────────────────┐                               │
│         ▼                  ▼                               │
│  ┌───────────┐      ┌───────────┐                          │
│  │Prometheus │      │Prometheus │                          │
│  │  Gauges   │      │ Counters  │                          │
│  │ (BA-4015) │      │ (BA-4014) │                          │
│  └───────────┘      └───────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   API Handler   │
                    │   (BA-4016)     │
                    │ Redis lookup →  │
                    │ fallback to API │
                    └─────────────────┘
```

### File Structure

```
src/ai/backend/storage/
├── volumes/
│   ├── stats/
│   │   ├── __init__.py
│   │   ├── types.py           # CachedFSPerfMetric, VolumeStatsObserverOptions
│   │   ├── observer.py        # VolumeStatsObserver (periodic observation)
│   │   └── state.py           # VolumeStatsState (cache lookup + fallback)
│   └── ...
└── ...
```

### Core Type Definitions (types.py)

```python
@dataclass
class VolumeStatsObserverOptions:
    """Volume stats observer configuration."""
    observe_interval: float = 10.0   # Observation interval (seconds)
    timeout_per_volume: float = 5.0  # Per-volume timeout (seconds)
    cache_ttl: float = 30.0          # Redis cache TTL (seconds)


@dataclass(frozen=True)
class CachedFSPerfMetric:
    """Cached performance metric with metadata."""
    volume_name: str
    metric: FSPerfMetric
    observed_at: datetime  # Actual observation timestamp
```

### VolumeStatsObserver (observer.py)

Handles periodic observation, referencing AbstractObserver:

```python
class VolumeStatsObserver:
    """Periodically observes performance metrics for all active volumes and stores in Redis."""

    @property
    def name(self) -> str:
        return "volume_stats"

    async def observe(self) -> None:
        """Observe metrics for all volumes and store in Redis."""
        ...

    def observe_interval(self) -> float:
        return self._options.observe_interval

    @classmethod
    def timeout(cls) -> float | None:
        return 30.0
```

### VolumeStatsState (state.py)

Handles cache lookup + external API fallback:

```python
class VolumeStatsState:
    """Volume stats state lookup. Redis cache first, then external API call."""

    async def get_performance_metric(
        self,
        volume_name: str,
    ) -> CachedFSPerfMetric:
        """
        Get performance metric.
        1. Try Redis cache lookup
        2. On cache miss or Redis failure, call external API directly
        3. Store external API result in Redis (suppress failures)
        """
        ...
```

### Prometheus Operational Metrics (inside observer.py)

Operational metrics to implement in BA-4014:

```python
# Counter: Observation attempt count (success/failure)
# name: backendai_storage_volume_stats_observe_total
# labels: volume, status (success|failure)

# Histogram: Observation duration
# name: backendai_storage_volume_stats_observe_duration_seconds
# labels: volume
# buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
```

### Configuration (config/unified.py)

Add to `StorageProxyConfig`:

```python
volume_stats_observe_interval: float = 10.0  # Observation interval (seconds)
volume_stats_observe_timeout: float = 5.0    # Per-volume timeout (seconds)
volume_stats_cache_ttl: float = 30.0         # Redis cache TTL (seconds)
```

## Error Handling Strategy

1. **Per-volume failure isolation**: Each volume has a separate Redis key, so failures are isolated
2. **TTL-based expiration**: Manage cache validity with Redis TTL instead of `is_stale` field
3. **Timeout**: 5-second per-volume timeout prevents blocking the entire loop
4. **Loop continuity**: Observer loop runs independently, continues even on exceptions

## Migration / Compatibility

### Backward Compatibility

- Existing `/volume/performance-metric` API response format maintained
- Only `observed_at` field added (BA-4016)

### Breaking Changes

None.

## Implementation Plan

Implementation order (dependency-based):

### Phase 1: BA-4014 - Periodic Observation Task

1. Create `volumes/stats/types.py`
   - `VolumeStatsObserverOptions`
   - `CachedFSPerfMetric`

2. Create `volumes/stats/observer.py`
   - `VolumeStatsObserver` class
   - Prometheus Counter, Histogram

3. Create `volumes/stats/state.py`
   - `VolumeStatsState` class (cache lookup + fallback)

4. Modify `config/unified.py`
   - Add configuration fields

5. Modify `context.py`
   - Add observer, state fields to `RootContext`

6. Modify `server.py`
   - Observer initialization and lifecycle management

### Phase 2: BA-4015 - Prometheus Performance Metrics

Expose data observed by Observer as Prometheus Gauges:
- `backendai_storage_volume_iops_read{volume}`
- `backendai_storage_volume_iops_write{volume}`
- `backendai_storage_volume_throughput_bytes_read{volume}`
- `backendai_storage_volume_throughput_bytes_write{volume}`
- `backendai_storage_volume_latency_usec_read{volume}`
- `backendai_storage_volume_latency_usec_write{volume}`
- `backendai_storage_volume_metric_last_updated_timestamp{volume}`

### Phase 3: BA-4013 - Redis Cache Layer

Redis cache already implemented in Phase 1. Minimal or no additional work needed.
- Cache key: `storage:perf_metric:{volume_name}`
- TTL: 30 seconds

### Phase 4: BA-4016 - API Modification

API returns data via VolumeStatsState:
- Redis cache hit: Return cached data + `observed_at`
- Redis cache miss/failure: Call external API directly

## Open Questions

1. **Leader election**: When multiple storage-proxy instances exist, each instance observes independently. Leader election left as future improvement.

## References

- [AbstractObserver](../src/ai/backend/common/observer/types.py) - Observer pattern reference
- [HealthProbe implementation](../src/ai/backend/common/health_checker/probe.py) - Periodic task pattern reference
