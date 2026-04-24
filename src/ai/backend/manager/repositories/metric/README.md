# Metric Repository Layer

## Overview

The Metric Repository provides the data access layer for metric-related operations in Backend.AI. It handles Prometheus queries for container utilization metrics and serves as a foundation for potential future database-backed metric storage.

## Current Implementation

### MetricRepository

- Queries Prometheus for kernel live stats (gauge/diff/rate metrics)
- Delegates platform fixed PromQL query construction to `FixedContainerQueryBuilder`
- Instantiated through the repository factory with `PrometheusClient` and a fixed query provider

### FixedContainerQueryBuilder

- Builds platform fixed container metric PromQL queries

### Metric data types

- Metric DTOs live in `ai.backend.manager.data.metric.types`
- `KernelMetricValuesByKernel`: Groups Prometheus response samples by kernel ID

## Usage

```python
from ai.backend.manager.repositories.metric.repository import MetricRepository

# Created in the repository factory with required dependencies
metric_repo = MetricRepository(
    db=db_engine,
    prometheus_client=prometheus_client,
    fixed_query_builder=fixed_query_builder,
)

# Query live stats for kernels
values_by_kernel = await metric_repo.query_container_live_stats(kernel_ids)
```
