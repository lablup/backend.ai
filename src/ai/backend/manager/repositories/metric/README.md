# Metric Repository Layer

## Overview

The Metric Repository provides the data access layer for metric-related operations in Backend.AI. Unlike other repositories that interact with database models, the metric repository serves as a foundation for potential future database-backed metric storage or caching mechanisms.

## Current Implementation

The current implementation consists of:

### MetricRepository
- Base repository class that holds a reference to the database engine
- Decorated with the metric layer-specific decorator
- Currently contains no methods as metrics are retrieved directly from Prometheus via the service layer

### MetricRepositories
- Factory class that creates and manages repository instances
- Follows the same pattern as other domain repositories for consistency
- Provides a `create()` method for instantiation

## Design Rationale

While the metric domain currently doesn't store data in the database (metrics are retrieved from Prometheus), the repository layer is maintained for:

1. **Consistency**: Follows the same architectural pattern as other domains
2. **Future Extension**: Provides a foundation for future features such as:
   - Metric metadata caching
   - User preferences for metric dashboards
   - Historical metric aggregations
   - Alert configurations

## Usage

```python
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.metric.repositories import MetricRepositories

# Create repository instances
args = RepositoryArgs(db=db_engine)
metric_repos = MetricRepositories.create(args)

# Access the metric repository
metric_repo = metric_repos.repository
```

## Testing

The repository layer includes tests for:
- Basic initialization
- Factory pattern implementation
- Dataclass structure
- Decorator functionality

## Future Considerations

When extending the metric repository with database operations:

1. **Add Models**: Create SQLAlchemy models for metric-related data
2. **Implement Methods**: Add repository methods decorated with `@repository_decorator()`
3. **Follow Patterns**: Use the same patterns as other repositories (e.g., user, group)
4. **Test Coverage**: Ensure comprehensive test coverage for new methods

Example future extension:
```python
@repository_decorator()
async def save_metric_preference(self, user_id: UUID, preferences: dict) -> None:
    """Save user's metric dashboard preferences."""
    # Implementation here

@repository_decorator()
async def get_metric_alerts(self, project_id: UUID) -> list[MetricAlert]:
    """Get metric alerts for a project."""
    # Implementation here
```