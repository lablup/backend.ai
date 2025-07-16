# Project Resource Policy Service

## Service Overview

The Project Resource Policy Service manages resource policies at the project level in Backend.AI. It provides functionality to create, modify, and delete resource policies that define resource limits and quotas for projects.

## Key Features and Capabilities

- **Create Project Resource Policies**: Define new resource policies with specific limits for projects
- **Modify Existing Policies**: Update resource limits and quotas for existing policies
- **Delete Policies**: Remove policies that are no longer needed
- **Resource Limit Management**: Control various resource aspects including:
  - Maximum vfolder count per project
  - Maximum quota scope size (total storage limit)
  - Maximum network count per project

## Operation Scenarios

### Creating a Project Resource Policy

When creating a new project resource policy, the service:
1. Accepts policy configuration through `CreateProjectResourcePolicyAction`
2. Validates the input parameters via `ProjectResourcePolicyCreator`
3. Persists the policy to the database through the repository layer
4. Returns the created policy data

### Modifying a Project Resource Policy

The modification process:
1. Receives modification request via `ModifyProjectResourcePolicyAction`
2. Uses `ProjectResourcePolicyModifier` to specify which fields to update
3. Retrieves the existing policy by name
4. Updates only the specified fields (partial updates supported)
5. Returns the updated policy data

### Deleting a Project Resource Policy

The deletion flow:
1. Accepts deletion request with policy name
2. Verifies the policy exists
3. Removes the policy from the database
4. Returns the deleted policy data for confirmation

## API Usage Examples

### Creating a Policy

```python
from ai.backend.manager.services.project_resource_policy.service import ProjectResourcePolicyService
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction
)
from ai.backend.manager.services.project_resource_policy.types import ProjectResourcePolicyCreator

# Create action
action = CreateProjectResourcePolicyAction(
    creator=ProjectResourcePolicyCreator(
        name="development-policy",
        max_vfolder_count=50,
        max_quota_scope_size=10737418240,  # 10GB
        max_vfolder_size=None,  # deprecated
        max_network_count=10
    )
)

# Execute
result = await service.create_project_resource_policy(action)
```

### Modifying a Policy

```python
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ProjectResourcePolicyModifier
)
from ai.backend.manager.types import OptionalState

# Partial update - only modify max_vfolder_count
action = ModifyProjectResourcePolicyAction(
    name="development-policy",
    modifier=ProjectResourcePolicyModifier(
        max_vfolder_count=OptionalState.update(100),
        # Other fields remain unchanged
    )
)

result = await service.modify_project_resource_policy(action)
```

### Deleting a Policy

```python
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction
)

action = DeleteProjectResourcePolicyAction(name="development-policy")
result = await service.delete_project_resource_policy(action)
```

## Integration Points

### Repository Layer

The service integrates with `ProjectResourcePolicyRepository` which provides:
- Database persistence with proper transaction handling
- Layer-aware decorators for monitoring and metrics
- Error handling for not-found scenarios

### Database Models

Uses `ProjectResourcePolicyRow` from the models layer which maps to the database schema:
- `name`: Unique policy identifier
- `max_vfolder_count`: Maximum number of vfolders allowed
- `max_quota_scope_size`: Total storage quota in bytes
- `max_network_count`: Maximum number of networks allowed

### Action System

The service follows the action-based pattern with:
- Separate action classes for each operation
- Result classes that extend `BaseActionResult`
- Entity ID tracking for audit purposes

## Testing Guidelines

### Unit Testing

The service includes comprehensive unit tests covering:
- Successful creation, modification, and deletion scenarios
- Error handling for non-existent policies
- Partial update functionality
- Integration with fixtures for database setup/teardown

### Test Fixtures

Key fixtures provided:
- `project_resource_policy_repository`: Repository instance
- `project_resource_policy_service`: Service instance
- `create_project_resource_policy`: Context manager for test data creation

### Running Tests

```bash
# Run all project resource policy tests
pytest tests/services/project_resource_policy/

# Run specific test
pytest tests/services/project_resource_policy/test_project_resource_policy.py::test_create_project_resource_policy
```

## Error Handling

The service handles the following error scenarios:
- `ObjectNotFound`: When attempting to modify or delete non-existent policies
- Database constraint violations: Handled at the repository layer
- Invalid input validation: Handled by action classes and type definitions

## Best Practices

1. **Use Partial Updates**: When modifying policies, only specify fields that need to change
2. **Handle Errors Gracefully**: Always catch `ObjectNotFound` exceptions in client code
3. **Resource Limits**: Set reasonable defaults for resource limits based on your infrastructure
4. **Policy Naming**: Use descriptive names that indicate the policy's purpose or target group