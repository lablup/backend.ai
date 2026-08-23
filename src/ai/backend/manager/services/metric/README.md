# Metric Service

## Service Overview

The Metric Service provides container utilization metrics collection and management for Backend.AI. It interfaces with Prometheus to query time-series data for various resource metrics including CPU, memory, network, and disk usage. The service is designed to support flexible querying, aggregation, and filtering of metrics data.

## Key Features and Capabilities

- **Metric Metadata Query**: Retrieve available metric names from the system
- **Time-Series Data Query**: Fetch historical metric data with customizable time ranges and intervals
- **Flexible Filtering**: Support for label-based filtering (kernel_id, agent_id, user_id, project_id, etc.)
- **Metric Type Detection**: Automatic detection and handling of different metric types (GAUGE, RATE, DIFF)
- **Aggregation Support**: Sum metrics by various dimensions for project/user level analysis
- **Prometheus Integration**: Direct integration with Prometheus for reliable metric storage and querying

## Operation Scenarios

### 1. List the metric names the store holds
```python
action = PublicSearchContainerMetricMetadataAction()
result = await metric_service.search_container_metric_metadata(action)
# Returns: ["container_cpu_percent", "container_memory_used_bytes", ...]
```

### 2. Read one metric over a time range
```python
action = PublicSearchContainerMetricsAction(
    metric_name="container_cpu_percent",
    labels=ContainerMetricOptionalLabel(kernel_id=kernel_id, value_type=ValueType.CURRENT),
    time_range=QueryTimeRange(
        start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
    ),
)
result = await metric_service.search_container_metrics(action)
```

The same action aggregates by any other label: pass `agent_id`, `session_id`,
`user_id` or `project_id` instead of `kernel_id`.

### 3. Read the latest stats of several kernels
```python
action = BatchGetKernelLiveStatsAction(kernel_ids=[kernel_id, other_kernel_id])
result = await metric_service.batch_get_kernel_live_stats(action)
```

## Action Inputs

| Action | Input |
|---|---|
| `PublicSearchContainerMetricMetadataAction` | none |
| `PublicSearchContainerMetricsAction` | `metric_name`, `labels`, `time_range` |
| `BatchGetKernelLiveStatsAction` | `kernel_ids` |

`ContainerMetricOptionalLabel` carries `value_type` plus the optional `agent_id`,
`kernel_id`, `session_id`, `user_id` and `project_id` filters;
`QueryTimeRange` carries `start`, `end` and `step`.

## Integration Points

### Prometheus Backend
- The service connects to Prometheus via HTTP API
- Endpoint configuration: `config.metric.address`
- Default timewindow for rate calculations: `config.metric.timewindow` (default: 1m)

### Metric Types and Automatic Detection
The service automatically determines metric types based on metric names:
- **GAUGE**: Default for most metrics (instant values)
- **RATE**: Applied to network metrics (net_rx, net_tx) for bytes/second calculation
- **DIFF**: Applied to CPU utilization when value_type="current" for percentage change

### Label System
All metrics use consistent labeling:
- `container_metric_name`: The metric being queried
- `value_type`: "usage" or "capacity"
- `agent_id`: Agent identifier
- `kernel_id`: Kernel identifier (Backend.AI's container wrapper, not the actual container ID)
- `session_id`: Session identifier
- `owner_user_id`: User identifier
- `owner_project_id`: Project identifier

## Testing Guidelines

### Unit Tests
The service includes comprehensive unit tests covering:
- Metadata query scenarios
- Various metric query patterns
- Error handling (connection failures, invalid queries)
- Metric type detection
- Query string generation

### Test Scenarios
1. **Basic Queries**: Single metric with simple filters
2. **Complex Filters**: Multiple label combinations
3. **Time Range Handling**: Various step sizes and time ranges
4. **Error Cases**: Network failures, invalid metrics, malformed queries
5. **Performance Scenarios**: Large time ranges, multiple kernels

### Running Tests
```bash
# Run metric service tests
pytest tests/services/metric/test_container_metric.py

# Run with coverage
pytest --cov=ai.backend.manager.services.metric tests/services/metric/
```

## Performance Considerations

### Query Optimization
1. **Step Size Selection**:
   - Short periods (< 1 hour): 30-60 second steps
   - Medium periods (1-24 hours): 5-15 minute steps
   - Long periods (> 24 hours): 1 hour steps

2. **Label Filtering**:
   - Always use specific labels when possible
   - Avoid wildcard patterns for better performance
   - Leverage Prometheus indexes

3. **Time Range Limits**:
   - Recommended maximum: 7 days
   - For longer periods, use pre-aggregated data
   - Consider implementing result pagination for large datasets

### Caching Strategy
- Prometheus handles caching internally
- Consider implementing application-level caching for frequently accessed metrics
- Cache metadata queries as metric names change infrequently

## Error Handling

### Common Errors
1. **FailedToGetMetric**: Raised when Prometheus query fails
   - Check Prometheus connectivity
   - Verify query syntax
   - Ensure requested metrics exist

2. **Connection Errors**: Network issues with Prometheus
   - Implement retry logic
   - Check firewall rules
   - Verify Prometheus is running

3. **Invalid Time Ranges**: Malformed or excessive time ranges
   - Validate input formats
   - Implement reasonable limits
   - Provide clear error messages

## Future Enhancements

1. **Metric Metadata Enhancement**:
   - Add metric descriptions
   - Include unit information
   - Define metric categories

2. **Advanced Aggregations**:
   - Percentile calculations
   - Moving averages
   - Anomaly detection

3. **Performance Improvements**:
   - Implement result streaming
   - Add query result caching
   - Support batch queries

4. **Extended Metric Support**:
   - Custom application metrics
   - External service metrics
   - Derived metrics calculations