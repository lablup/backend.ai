---
Author: BoKeum Kim (bkkim@lablup.com)
Status: Draft
Created: 2026-02-03
Created-Version: 26.2.0
Target-Version:
Implemented-Version:
---

# Prometheus Client Extraction and Querier Interface Abstraction

## Motivation

The `ContainerUtilizationMetricService` previously contained both business logic and Prometheus-specific query building logic tightly coupled together. This made it difficult to:

1. **Extend to other metric types**: Adding new metric sources (e.g., agent metrics, node metrics) would require duplicating query building logic
2. **Test in isolation**: The service mixed HTTP communication, query string generation, and metric type detection
3. **Maintain single responsibility**: One class handled too many concerns

The refactoring aims to:
- Separate metric identification (what to query) from query execution (how to query)
- Create an extensible interface hierarchy for different metric querier types
- Enable the Prometheus client to work with any querier implementing the interface

## Current Design

On main branch, there is **no dedicated Prometheus client**. All logic resides in `ContainerUtilizationMetricService`:

```
ContainerUtilizationMetricService
    ├── _query_label_values()                    # Direct aiohttp call
    ├── _get_query_string()                      # Query building orchestration
    ├── _parse_query_string_by_metric_spec()     # PromQL string generation
    ├── _get_metric_type()                       # Metric type detection
    ├── _get_label_values_for_query()            # Label selector building
    ├── _get_sum_by_for_query()                  # Group by clause building
    └── query_metric()                           # Direct aiohttp call with inline error handling
```

**Problems:**
1. **No separation of concerns**: HTTP communication, query building, and business logic all mixed in one service
2. **Direct aiohttp usage**: Each request creates a new `ClientSession`, no connection pooling
3. **Not reusable**: Cannot share Prometheus access logic with other services
4. **Hard to test**: Must mock aiohttp internals to test query building logic
5. **No extensibility**: Adding new metric types (agent, node) would require duplicating everything

## Proposed Design

### Interface Hierarchy

```
PrometheusMetricQuerier (ABC)
    │   ├── name() → str              # Prometheus metric name
    │   └── labels() → dict[str, str] # Label selectors
    │
    └── AggregatingMetricQuerier (ABC)
            │   └── group_by_labels() → list[str]  # For sum by, avg by
            │
            └── UtilizationMetricQuerier (ABC)
                    └── query_strategy() → QueryStrategy  # gauge/rate/rate_normalized
```

### New Type Definitions

```python
# clients/prometheus/types.py

class QueryStrategy(StrEnum):
    """Query strategy for utilization metrics."""
    GAUGE = "gauge"              # Instant value (mem_used, gpu_mem)
    RATE = "rate"                # Rate of change (cpu_util)
    RATE_NORMALIZED = "rate_normalized"  # Rate / interval (net_rx, net_tx)

@dataclass(frozen=True)
class QueryTimeRange:
    """Time range parameters for Prometheus queries."""
    start: str
    end: str
    step: str

class PrometheusMetricQuerier(ABC):
    """Base interface for metric identification."""

    @abstractmethod
    def name(self) -> str:
        """Return the Prometheus metric name."""
        ...

    @abstractmethod
    def labels(self) -> dict[str, str]:
        """Return label selectors for filtering."""
        ...

class AggregatingMetricQuerier(PrometheusMetricQuerier):
    """Interface for queries that support aggregation."""

    @abstractmethod
    def group_by_labels(self) -> list[str]:
        """Return labels to group by when aggregating."""
        ...

class UtilizationMetricQuerier(AggregatingMetricQuerier):
    """Interface for utilization metrics that know their query strategy."""

    @abstractmethod
    def query_strategy(self) -> QueryStrategy:
        """Return the query strategy for this metric."""
        ...
```

### Concrete Implementation

```python
@dataclass(kw_only=True)
class ContainerMetricQuerier(UtilizationMetricQuerier):
    """Querier for container-level utilization metrics."""

    metric_name: str
    value_type: str  # "current" or "capacity"
    kernel_id: UUID | None = None
    agent_id: str | None = None
    session_id: UUID | None = None
    user_id: UUID | None = None
    project_id: UUID | None = None

    @override
    def name(self) -> str:
        return "backendai_container_utilization"

    @override
    def labels(self) -> dict[str, str]:
        result = {
            "container_metric_name": self.metric_name,
            "value_type": self.value_type,
        }
        if self.kernel_id is not None:
            result["kernel_id"] = str(self.kernel_id)
        # ... other optional labels
        return result

    @override
    def group_by_labels(self) -> list[str]:
        group_by = ["value_type"]
        if self.kernel_id is not None:
            group_by.append("kernel_id")
        # ... other optional labels
        return group_by

    @override
    def query_strategy(self) -> QueryStrategy:
        match self.metric_name:
            case "cpu_util":
                return QueryStrategy.RATE
            case "net_rx" | "net_tx":
                return QueryStrategy.RATE_NORMALIZED
            case _:
                return QueryStrategy.GAUGE
```

### Unified PrometheusClient

```python
class PrometheusClient:

    _client_pool: ClientPool # Using client pool
    _client_key: ClientKey

    # ── Public API ──────────────────────────────────────────────────
    async def query_utilization(
        self,
        querier: UtilizationMetricQuerier,
        time_range: QueryTimeRange,
        *,
        rate_interval: str = "5m",
    ) -> PrometheusQueryRangeResponse:
        """Query utilization metrics with automatic strategy selection."""
        match querier.query_strategy():
            case QueryStrategy.RATE:
                return await self._query_rate(querier, time_range, rate_interval)
            ...

    async def query_available_container_metrics(self) -> list[str]:
        """Fetch list of available container metric names."""
        ...

    # ── Private: Query Building ─────────────────────────────────────
    async def _query_gauge(self, querier, time_range): ...
    async def _query_rate(self, querier, time_range, interval, *, normalize=False): ...

    # ── Private: HTTP Transport ─────────────────────────────────────
    async def _post(self, path, *, data=None, request_timeout=None): ...
    async def _get(self, path, *, params=None, request_timeout=None): ...
```

### Simplified Service Layer

```python
class ContainerUtilizationMetricService:
    """Thin coordination layer - delegates to client."""

    async def fetch_metric(self, action: ContainerMetricAction):
        querier = ContainerMetricQuerier(
            metric_name=action.metric_name,
            value_type=action.labels.value_type,
            kernel_id=action.labels.kernel_id,
            # ... map action to querier
        )
        time_range = QueryTimeRange(
            start=action.start,
            end=action.end,
            step=action.step,
        )
        result = await self._prometheus_client.query_utilization(
            querier, time_range, rate_interval=self._rate_interval
        )
        # ... transform result
```

## Migration / Compatibility

### Backward Compatibility

- **Internal API change**: `query_range()` and `query_label_values()` removed from public API
- **No external impact**: These methods were only used by `ContainerUtilizationMetricService`
- **Service API unchanged**: `ContainerUtilizationMetricService.query_metric()` signature preserved

### Removed Types

The following types were removed from `services/metric/types.py`:
- `UtilizationMetricType` enum → Replaced by `QueryStrategy` in `clients/prometheus/types.py`
- `MetricSpecForQuery` dataclass → Logic moved to `ContainerMetricQuerier`

## Extensibility Example

Adding a new metric querier requires no client changes:

```python
@dataclass(kw_only=True)
class NodeMetricQuerier(UtilizationMetricQuerier):
    """Querier for node-level metrics."""

    metric_name: str
    node_id: str

    ...

# Usage - client unchanged
result = await prometheus_client.query_utilization(
    NodeMetricQuerier(metric_name="cpu_usage", node_id="node-001"),
    time_range,
)
```
