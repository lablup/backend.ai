# Metric Repository Layer

## Overview

The Metric Repository provides the data access layer for metric-related operations in Backend.AI. It handles metric queries for container utilization metrics and serves as a foundation for potential future database-backed metric storage.

## Current Implementation

### MetricRepository

- Queries metric backend for kernel live stats (gauge/diff/rate metrics)
- Delegates metric queries to `PrometheusClient`
- Instantiated through the repository factory

### PrometheusClient

- Receives `FixedQueryBuilder` during dependency initialization
- Exposes `fetch_*` methods for container metric data
- Keeps raw Prometheus query execution methods private

### FixedQueryBuilder

- Builds platform fixed container metric PromQL queries

### Metric data types

- Metric DTOs live in `ai.backend.common.clients.prometheus.metric_types`
- `KernelLiveStatBatchResult`: Groups live-stat query results by kernel ID

## Usage

```python
from ai.backend.manager.repositories.metric.repository import MetricRepository

# Created in the repository factory with required dependencies.
metric_repo = MetricRepository(
    db=db_engine,
    prometheus_client=prometheus_client,
)

# Query live stats for kernels
values_by_kernel = await metric_repo.query_container_live_stats(kernel_ids)
```
