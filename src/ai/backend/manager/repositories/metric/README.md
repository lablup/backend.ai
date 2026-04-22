# Metric Repository Layer

## Overview

The Metric Repository provides the data access layer for metric-related operations in Backend.AI. It handles Prometheus queries for container utilization metrics and serves as a foundation for potential future database-backed metric storage.

## Current Implementation

### MetricRepository

- Queries Prometheus for kernel live stats (gauge/diff/rate metrics)
- Builds PromQL presets and parses responses into `MetricValue` types
- Instantiated directly in the service factory with `PrometheusClient` and `timewindow`

### Types (`types.py`)

- `KernelMetricValuesByKernel`: Groups Prometheus response samples by kernel ID

## Usage

```python
from ai.backend.manager.repositories.metric.repository import MetricRepository

# Created in the service factory with required dependencies
metric_repo = MetricRepository(
    db=db_engine,
    prometheus_client=prometheus_client,
    timewindow="1m",
)

# Query live stats for kernels
values_by_kernel = await metric_repo.query_kernel_live_stats(kernel_ids)
```
