# User Resource Policy Service

## Service Overview

The User Resource Policy Service manages resource policies that apply to users in Backend.AI. These policies define resource limits and quotas that control how many resources individual users can consume.

## Key Features and Capabilities

- **Create User Resource Policies**: Define new resource policies with specific limits for user resources
- **Modify User Resource Policies**: Update existing policies with new resource limits
- **Delete User Resource Policies**: Remove policies that are no longer needed
- **Repository Pattern**: Uses a clean architecture with repository pattern for data access

### Resource Limits Supported

- `max_vfolder_count`: Maximum number of virtual folders a user can create
- `max_quota_scope_size`: Maximum total size quota for all user resources
- `max_session_count_per_model_session`: Maximum number of sessions per model session
- `max_customized_image_count`: Maximum number of custom images a user can create

Note: `max_vfolder_size` field is deprecated and not used in the current implementation.

## Operation Scenarios

### Creating a User Resource Policy

When an administrator needs to define a new resource policy for users:

1. Create a `UserResourcePolicyCreator` with the desired limits
2. Execute `CreateUserResourcePolicyAction` through the service
3. The service creates the policy in the database via the repository
4. Returns `CreateUserResourcePolicyActionResult` with the created policy data

### Modifying a User Resource Policy

When resource limits need to be adjusted:

1. Create a `UserResourcePolicyModifier` with fields to update
2. Execute `ModifyUserResourcePolicyAction` with the policy name
3. The service updates only the specified fields via the repository
4. Returns `ModifyUserResourcePolicyActionResult` with updated policy data

### Deleting a User Resource Policy

When a policy is no longer needed:

1. Execute `DeleteUserResourcePolicyAction` with the policy name
2. The service removes the policy from the database
3. Returns `DeleteUserResourcePolicyActionResult` with the deleted policy data

## API Usage Examples

### Create User Resource Policy

```python
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.repositories.user_resource_policy.creators import UserResourcePolicyCreatorSpec

# Create a new policy with specific limits
creator = UserResourcePolicyCreatorSpec(
    name="standard-user-policy",
    max_vfolder_count=50,
    max_quota_scope_size=10737418240,  # 10GB
    max_session_count_per_model_session=5,
    max_customized_image_count=10,
)

action = CreateUserResourcePolicyAction(creator=creator)
result = await user_resource_policy_service.create_user_resource_policy(action)
```

### Modify User Resource Policy

```python
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    UserResourcePolicyModifier,
)
from ai.backend.manager.types import OptionalState

# Update specific fields of an existing policy
modifier = UserResourcePolicyModifier(
    max_vfolder_count=OptionalState.update(100),  # Increase limit
    max_quota_scope_size=OptionalState.update(21474836480),  # 20GB
    max_session_count_per_model_session=OptionalState.update(None),  # Remove limit
)

action = ModifyUserResourcePolicyAction(
    name="standard-user-policy",
    modifier=modifier,
)
result = await user_resource_policy_service.modify_user_resource_policy(action)
```

### Delete User Resource Policy

```python
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)

action = DeleteUserResourcePolicyAction(name="obsolete-policy")
result = await user_resource_policy_service.delete_user_resource_policy(action)
```

## Integration Points

### Repository Layer

The service integrates with `UserResourcePolicyRepository` for all data operations:

- `create()`: Creates new policies
- `update()`: Updates existing policies
- `delete()`: Removes policies

### Action Processing

The service is used through `UserResourcePolicyProcessors` which wraps service methods with:

- Action monitoring capabilities
- Asynchronous processing support
- Consistent error handling

### Database Models

The service works with `UserResourcePolicyRow` model from `ai.backend.manager.models.resource_policy`.

## Testing Guidelines

### Unit Testing

Test files are located in `tests/services/user_resource_policy/`. Key test scenarios include:

1. **Create Policy Tests**:
   - Valid data creation
   - Minimal data creation
   - Duplicate name handling

2. **Modify Policy Tests**:
   - Updating specific fields
   - Unsetting fields
   - Non-existing policy handling

3. **Delete Policy Tests**:
   - Successful deletion
   - Non-existing policy handling

### Test Fixtures

- `create_user_resource_policy`: Context manager for creating test policies
- `processors`: Provides configured service processors for testing

### Running Tests

```bash
# Run all user resource policy tests
pytest tests/services/user_resource_policy/

# Run specific test
pytest tests/services/user_resource_policy/test_user_resource_policy.py::test_create_user_resource_policy
```

### Error Handling

The service properly handles:

- `ObjectNotFound`: When trying to modify/delete non-existing policies
- `IntegrityError`: When creating policies with duplicate names
- Repository-level exceptions are propagated to callers