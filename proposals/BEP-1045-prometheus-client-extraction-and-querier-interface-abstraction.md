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
- Create a template-based query system where PromQL patterns are defined as presets
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

### Overview

The design separates concerns into:
- **MetricQuerier**: Abstract interface defining what metric to query
- **MetricPreset**: Defines PromQL template and allowed placeholders (defined elsewhere)
- **MetricQueryInput**: User-provided query parameters
- **PrometheusClient**: Renders template and executes HTTP request

### MetricQuerier ABC

`MetricQuerier` is an abstract base class that defines what metric to query. It provides the common interface for metric identification — name, label selectors, and grouping labels.

```python
# clients/prometheus/types.py

class MetricQuerier(ABC):
    """Abstract interface for metric query specification."""

    @abstractmethod
    def name(self) -> str:
        """Return the Prometheus metric name."""
        ...

    @abstractmethod
    def labels(self) -> dict[str, str]:
        """Return label selectors for filtering."""
        ...

    @abstractmethod
    def group_by_labels(self) -> list[str]:
        """Return labels to group by when aggregating."""
        ...
```

### ContainerMetricQuerier

`ContainerMetricQuerier` is a concrete implementation for container-level utilization metrics:

```python
# clients/prometheus/querier.py

@dataclass(kw_only=True)
class ContainerMetricQuerier(MetricQuerier):
    """Querier for container-level utilization metrics."""

    metric_name: str
    value_type: str
    kernel_id: UUID | None = None
    # ... other optional fields

    @override
    def name(self) -> str:
        return "backendai_container_utilization"

    @override
    def labels(self) -> dict[str, str]:
        # Build label selectors from fields
        ...

    @override
    def group_by_labels(self) -> list[str]:
        # Return labels to group by
        ...
```

### Type Definitions

```python
# clients/prometheus/types.py


@dataclass(frozen=True)
class QueryTimeRange:
    """Time range parameters for Prometheus range queries."""
    start: str
    end: str
    step: str
```

### PrometheusClient

`PrometheusClient` takes a `MetricPreset`, `MetricQuerier`, and `window` parameter to render and execute the query. The client uses the querier's `name()`, `labels()`, `group_by_labels()` to fill the preset template.

```python
# clients/prometheus/client.py

class PrometheusClient:

    _client_pool: ClientPool
    _client_key: ClientKey

    async def query_range(
        self,
        preset: MetricPreset,
        querier: MetricQuerier,
        time_range: QueryTimeRange,
        *,
        window: str = "5m",
    ) -> PrometheusQueryRangeResponse:
        """Execute a Prometheus range query."""
        query = self._render_query(preset, querier, window)
        return await self._post("/api/v1/query_range", data={
            "query": query,
            "start": time_range.start,
            "end": time_range.end,
            "step": time_range.step,
        })

    def _render_query(preset: MetricPreset, querier: MetricQuerier, window: str) -> str:
        """Simple template substitution using querier interface."""
        labels_str = ",".join(f'{k}="{v}"' for k, v in querier.labels().items())
        group_by_str = ",".join(querier.group_by_labels())

        return preset.query_template.format(
            metric_name=querier.name(),
            labels=labels_str,
            group_by=group_by_str,
            window=window,
        )
```

**PromQL rendering examples:**

| Preset Template | Input | Rendered PromQL |
|---|---|---|
| `sum by ({group_by})(rate({metric_name}{{{labels}}}[{window}]))` | `labels={"endpoint": "/auth"}, group_by=["endpoint"], window="1m"` | `sum by (endpoint)(rate(backendai_api_request_count_total{endpoint="/auth"}[1m]))` |
| `{metric_name}{{{labels}}}` | `labels={"value_type": "current"}, group_by=[], window="5m"` | `backendai_container_utilization{value_type="current"}` |

### Simplified Service Layer

The `ContainerUtilizationMetricService` becomes a thin coordination layer that delegates to `PrometheusClient`:

```python
# services/metric/container_metric.py

class ContainerUtilizationMetricService:
    """Thin coordination layer - delegates to client."""

    _prometheus_client: PrometheusClient

    async def fetch_metric(self, action: ContainerMetricAction) -> ContainerMetricActionResult:
        querier = ContainerMetricQuerier(
            metric_name=action.metric_name,
            value_type=action.labels.value_type,
            kernel_id=action.labels.kernel_id,
            ...
        )
        time_range = QueryTimeRange(start=action.start, end=action.end, step=action.step)
        # Legacy: preset is hardcoded until MetricPreset system is implemented
        result = await self._prometheus_client.query_range(
            CONTAINER_METRIC_PRESET, querier, time_range, window=self._rate_interval
        )
        # ... transform result
```

## Migration / Compatibility

### Backward Compatibility

- **Internal API change**: Direct query building methods removed from service layer
- **No external impact**: `ContainerUtilizationMetricService.fetch_metric()` signature preserved
- **Service API unchanged**: All callers continue to work without modification

### Removed Types

The following types are removed from `services/metric/types.py`:
- `UtilizationMetricType` enum → Replaced by preset's query template
- `MetricSpecForQuery` dataclass → Replaced by `MetricQuerier` interface
