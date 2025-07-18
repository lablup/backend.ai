# Group Service

## Service Overview

The Group Service manages groups (also known as projects) in Backend.AI. It provides comprehensive functionality to create, modify, delete, and purge groups, as well as retrieve resource usage statistics. Groups serve as organizational units that contain users and manage resources, permissions, and policies within the Backend.AI platform.

## Key Features and Capabilities

- **Create Groups**: Define new groups with specific configurations and resource policies
- **Modify Existing Groups**: Update group properties, membership, and configurations
- **Delete Groups**: Mark groups as inactive (soft delete) while preserving data
- **Purge Groups**: Permanently remove groups and associated data with dependency checks
- **Resource Usage Analytics**: Track and analyze resource consumption over time
- **User Management**: Add, remove, and manage users within groups
- **Resource Policy Management**: Control resource limits and quotas at the group level
- **Multi-Domain Support**: Manage groups across different domains
- **Integration Support**: Handle external system integrations via integration IDs

## Operation Scenarios

### Creating a Group

When creating a new group, the service:
1. Accepts group configuration through `CreateGroupAction`
2. Validates the input parameters via `GroupCreator`
3. Persists the group to the database through the repository layer
4. Returns the created group data with success status

### Modifying a Group

The modification process:
1. Receives modification request via `ModifyGroupAction`
2. Uses `GroupModifier` to specify which fields to update
3. Supports user membership updates with different modes (add, remove, replace)
4. Converts user UUID strings to proper UUID objects for validation
5. Updates only the specified fields (partial updates supported)
6. Returns the updated group data

### Deleting a Group

The deletion flow (soft delete):
1. Accepts deletion request with group ID
2. Marks the group as inactive rather than physical deletion
3. Preserves group data and relationships for potential recovery
4. Returns success status

### Purging a Group

The purge operation (hard delete):
1. Performs comprehensive dependency checks:
   - Verifies no active kernels are running
   - Ensures no vfolders are mounted to active kernels
   - Checks for no active endpoints
2. Permanently removes the group and associated data
3. Raises specific exceptions for dependency violations
4. Returns success status upon completion

### Resource Usage Analytics

The service provides two types of usage analytics:

#### Usage Per Month
- Retrieves resource usage statistics for specified month
- Supports filtering by group IDs
- Returns container statistics for the entire month period

#### Usage Per Period
- Provides detailed resource usage for custom date ranges
- Supports up to 100-day query periods
- Returns project-level resource consumption data
- Includes CPU, memory, and other resource metrics

## API Usage Examples

### Creating a Group

```python
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.group.actions.create_group import CreateGroupAction
from ai.backend.manager.services.group.types import GroupCreator
from ai.backend.manager.models.group import ProjectType
from ai.backend.common.types import ResourceSlot

# Create action
action = CreateGroupAction(
    input=GroupCreator(
        name="development-team",
        domain_name="example.com",
        type=ProjectType.GENERAL,
        description="Development team group",
        is_active=True,
        total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
        allowed_vfolder_hosts={"local": "local"},
        resource_policy="development-policy",
        container_registry={"registry": "docker.io"}
    )
)

# Execute
result = await service.create_group(action)
```

### Modifying a Group

```python
from ai.backend.manager.services.group.actions.modify_group import ModifyGroupAction
from ai.backend.manager.services.group.types import GroupModifier
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.manager.models.user import UserUpdateMode
from uuid import UUID

# Partial update - modify description and add users
action = ModifyGroupAction(
    group_id=UUID("12345678-1234-1234-1234-123456789012"),
    modifier=GroupModifier(
        description=TriState.update("Updated development team description"),
        total_resource_slots=OptionalState.update(ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None))
    ),
    user_update_mode=OptionalState.update(UserUpdateMode.ADD),
    user_uuids=OptionalState.update(["user-uuid-1", "user-uuid-2"])
)

result = await service.modify_group(action)
```

### Deleting a Group

```python
from ai.backend.manager.services.group.actions.delete_group import DeleteGroupAction
from uuid import UUID

action = DeleteGroupAction(group_id=UUID("12345678-1234-1234-1234-123456789012"))
result = await service.delete_group(action)
```

### Purging a Group

```python
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionActiveKernelsError,
    PurgeGroupActionActiveEndpointsError,
    PurgeGroupActionVFoldersMountedToActiveKernelsError
)
from uuid import UUID

action = PurgeGroupAction(group_id=UUID("12345678-1234-1234-1234-123456789012"))

try:
    result = await service.purge_group(action)
except PurgeGroupActionActiveKernelsError:
    # Handle active kernels error
    pass
except PurgeGroupActionActiveEndpointsError:
    # Handle active endpoints error
    pass
except PurgeGroupActionVFoldersMountedToActiveKernelsError:
    # Handle mounted vfolders error
    pass
```

### Resource Usage Analytics

```python
from ai.backend.manager.services.group.actions.usage_per_month import UsagePerMonthAction
from ai.backend.manager.services.group.actions.usage_per_period import UsagePerPeriodAction
from uuid import UUID

# Monthly usage
monthly_action = UsagePerMonthAction(
    month="202410",  # October 2024
    group_ids=[UUID("12345678-1234-1234-1234-123456789012")]
)
monthly_result = await service.usage_per_month(monthly_action)

# Period usage
period_action = UsagePerPeriodAction(
    start_date="20241001",
    end_date="20241031",
    project_id=UUID("12345678-1234-1234-1234-123456789012")
)
period_result = await service.usage_per_period(period_action)
```

## Integration Points

### Repository Layer

The service integrates with two main repository classes:

#### GroupRepository
- Standard group operations (create, modify, delete)
- Resource usage statistics retrieval
- User membership management
- Query operations with filtering and pagination

#### AdminGroupRepository
- Administrative operations requiring elevated permissions
- Force purge operations with dependency checks
- System-level group management

### Database Models

Uses `GroupRow` from the models layer which maps to the database schema:
- `id`: Unique group identifier (UUID, primary key)
- `name`: Group name (unique constraint)
- `domain_name`: Associated domain (foreign key)
- `description`: Optional group description
- `is_active`: Active status for soft deletion
- `type`: Project type (GENERAL, MODEL_STORE)
- `total_resource_slots`: Resource allocation limits
- `allowed_vfolder_hosts`: Permitted storage hosts
- `resource_policy`: Associated resource policy name
- `container_registry`: Container registry configuration
- `integration_id`: External system integration identifier
- `created_at`/`modified_at`: Timestamp tracking

### External Dependencies

#### ValkeyStatClient
- Resource usage statistics collection
- Performance metrics aggregation
- Real-time monitoring data

#### StorageSessionManager
- Storage resource management
- VFolder operations coordination
- Storage policy enforcement

#### ManagerConfigProvider
- System configuration access
- Timezone and locale settings
- Resource limits and defaults

### Action System

The service follows the action-based pattern with:
- Separate action classes for each operation type
- Result classes extending `BaseActionResult`
- Entity ID tracking for audit and monitoring
- Standardized error handling and logging

## Testing Guidelines

### Test Coverage

The project includes comprehensive test coverage at multiple layers:

#### Service Layer Tests
- Integration tests through service actions
- End-to-end workflow validation
- Error handling and exception scenarios
- Resource usage analytics validation

#### Repository Layer Tests
- Direct repository method testing
- Database constraint validation
- Concurrent operation handling
- Transaction rollback scenarios
- Complex query operations

### Test Fixtures

Key fixtures provided for reliable test data management:
- `group_repository`: Standard group repository instance
- `admin_group_repository`: Admin group repository instance
- `group_service`: Complete service instance with dependencies
- `create_group`: Async context manager for test group creation with cleanup
- `database_fixture`: Database setup with proper isolation

### Test Data Management

Tests use fixture-based patterns to ensure:
- Proper cleanup of test data after completion
- Isolation between test cases
- Consistent database state
- Mock external dependencies (ValkeyStatClient, StorageSessionManager)

### Running Tests

```bash
# Run repository tests
pytest tests/manager/repositories/group/test_group.py

# Run service tests
pytest tests/manager/services/group/

# Run with coverage
pytest --cov=ai.backend.manager.services.group \
       --cov=ai.backend.manager.repositories.group
```

## Error Handling

The service provides comprehensive error handling for various scenarios:

### Service Layer Errors

#### GroupNotFound
- Raised when attempting to modify or delete non-existent groups
- Handled gracefully with appropriate logging
- Returns failure status in action results

#### Dependency Violations (Purge Operations)
- `PurgeGroupActionActiveKernelsError`: Active kernels prevent purge
- `PurgeGroupActionActiveEndpointsError`: Active endpoints prevent purge
- `PurgeGroupActionVFoldersMountedToActiveKernelsError`: Mounted vfolders prevent purge

#### Validation Errors
- `InvalidAPIParameters`: Invalid date formats or ranges
- Input validation through action classes and type definitions

### Repository Layer Errors
- `IntegrityError`: Duplicate group names or constraint violations
- `DatabaseError`: Connection or transaction failures
- `ObjectNotFound`: Group lookup failures

### Usage Analytics Errors
- Date range validation (maximum 100 days)
- Invalid date format handling
- Timezone conversion errors

## Best Practices

1. **Group Management**:
   - Use descriptive group names that indicate purpose or team
   - Set appropriate resource limits based on actual needs
   - Regularly review and update group configurations

2. **User Membership**:
   - Use specific user update modes (ADD, REMOVE, REPLACE) appropriately
   - Validate user UUIDs before adding to groups
   - Handle user membership changes atomically

3. **Resource Policies**:
   - Align group resource policies with organizational needs
   - Monitor resource usage to optimize allocations
   - Update policies based on usage patterns

4. **Deletion vs Purging**:
   - Use soft delete (delete_group) for most scenarios
   - Reserve purge operations for permanent cleanup
   - Always check dependencies before purging
   - Implement proper approval workflows for purge operations

5. **Error Handling**:
   - Always catch and handle specific exceptions
   - Log errors appropriately for debugging
   - Provide meaningful error messages to users
   - Implement retry mechanisms for transient failures

6. **Testing**:
   - Use provided fixtures for consistent test data
   - Test both success and failure scenarios
   - Validate cleanup operations
   - Mock external dependencies appropriately

7. **Performance**:
   - Use appropriate date ranges for usage queries
   - Implement pagination for large result sets
   - Cache frequently accessed group data
   - Monitor resource usage query performance

8. **Security**:
   - Validate user permissions before group operations
   - Audit group membership changes
   - Protect sensitive group configurations
   - Implement proper access controls for admin operations