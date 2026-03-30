# User Service

## Service Overview

The User Service is a core component of Backend.AI that handles comprehensive user account management operations. It provides a robust, action-based architecture for creating, modifying, deleting, and managing user accounts, along with advanced features like resource usage statistics and user data purging.

## Key Features and Capabilities

### Core User Management
- **User Creation**: Create new user accounts with customizable properties
- **User Modification**: Update user information, roles, and permissions
- **User Deletion**: Soft delete users while preserving audit trails
- **User Purging**: Permanently remove users and all associated resources

### Advanced Features
- **Resource Usage Statistics**: Detailed monthly usage tracking per user
- **Admin Statistics**: System-wide usage analytics and monitoring
- **Container Configuration**: Support for custom UID/GID settings
- **Security Features**: TOTP authentication, IP restrictions, and sudo session control

### Architecture
- **Action-Based Design**: Each operation is encapsulated in typed action classes
- **Repository Pattern**: Clean separation between business logic and data access
- **Processor Pattern**: Asynchronous processing with monitoring capabilities
- **Type Safety**: Comprehensive type definitions for all operations

## Operation Scenarios

### 1. User Creation

#### Basic User Creation
```python
from ai.backend.manager.services.user.actions.create_user import CreateUserAction
from ai.backend.manager.services.user.type import UserCreator

action = CreateUserAction(
    input=UserCreator(
        email="user@example.com",
        password="SecurePassword123!",
        username="newuser",
        full_name="New User",
        domain_name="default",
        need_password_change=False,
        role=UserRole.USER,
        resource_policy="default-policy",
    )
)

result = await user_processor.create_user.wait_for_complete(action)
```

#### Admin User with Special Permissions
```python
action = CreateUserAction(
    input=UserCreator(
        email="admin@example.com",
        password="AdminPass123!",
        username="admin",
        full_name="System Administrator",
        domain_name="default",
        need_password_change=False,
        role=UserRole.ADMIN,
        sudo_session_enabled=True,
        resource_policy="admin-policy",
    )
)
```

#### User with Container Configuration
```python
action = CreateUserAction(
    input=UserCreator(
        email="container@example.com",
        password="ContainerPass123!",
        username="containeruser",
        domain_name="default",
        need_password_change=False,
        container_uid=2000,
        container_main_gid=2000,
        container_gids=[2000, 2001],
        allowed_client_ip=["192.168.1.0/24"],
    )
)
```

### 2. User Modification

#### Basic Information Updates
```python
from ai.backend.manager.services.user.actions.modify_user import ModifyUserAction, UserModifier
from ai.backend.manager.types import OptionalState

action = ModifyUserAction(
    email="user@example.com",
    modifier=UserModifier(
        full_name=OptionalState.update("Updated Name"),
        description=OptionalState.update("Senior Developer"),
    ),
)
```

#### Role and Permission Changes
```python
action = ModifyUserAction(
    email="user@example.com",
    modifier=UserModifier(
        role=OptionalState.update(UserRole.ADMIN),
        sudo_session_enabled=OptionalState.update(True),
    ),
)
```

#### Security Settings
```python
action = ModifyUserAction(
    email="user@example.com",
    modifier=UserModifier(
        totp_activated=OptionalState.update(True),
        need_password_change=OptionalState.update(True),
        status=OptionalState.update(UserStatus.ACTIVE),
    ),
)
```

### 3. User Deletion

#### Soft Delete (Preserves Data)
```python
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction

action = DeleteUserAction(email="user@example.com")
result = await user_processor.delete_user.wait_for_complete(action)
```

### 4. User Purging

#### Complete User Removal
```python
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.user.type import UserInfoContext

action = PurgeUserAction(
    email="user@example.com",
    user_info_ctx=UserInfoContext(
        uuid=user_uuid,
        email="user@example.com",
        main_access_key=user_access_key,
    ),
)
```

### 5. Usage Statistics

#### User Monthly Statistics
```python
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction

action = UserMonthStatsAction(user_id=str(user_uuid))
result = await user_processor.user_month_stats.wait_for_complete(action)
```

#### Admin System Statistics
```python
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction

action = AdminMonthStatsAction()
result = await user_processor.admin_month_stats.wait_for_complete(action)
```

## API Usage Examples

### Initialization
```python
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user.processors import UserProcessors

# Initialize service with required dependencies
user_service = UserService(
    storage_manager=storage_manager,
    valkey_stat_client=valkey_client,
    agent_registry=agent_registry,
    user_repository=user_repository,
    admin_user_repository=admin_user_repository,
)

# Create processors for async operations
processors = UserProcessors(
    user_service=user_service,
    action_monitors=[monitor],
)
```

### Error Handling
```python
try:
    result = await processors.create_user.wait_for_complete(action)
    if result.success:
        user_data = result.data
        print(f"User created: {user_data.email}")
    else:
        print("User creation failed")
except Exception as e:
    print(f"Error: {e}")
```

## Integration Points

### Database Integration
- **User Repository**: Handles user CRUD operations
- **Admin Repository**: Manages admin-level operations and force operations
- **Transaction Management**: Supports database transactions for data consistency

### External Service Integration
- **Valkey/Redis**: Usage statistics and caching
- **Agent Registry**: Session management and resource allocation
- **Storage Manager**: VFolder management and storage operations

### Security Integration
- **TOTP**: Two-factor authentication support
- **IP Restrictions**: Client IP-based access control
- **Role-Based Access**: Admin, user, and monitor role management

## Testing Guidelines

### Unit Testing
```python
import pytest
from tests.manager.services.test_utils import ScenarioBase

@pytest.mark.parametrize("test_scenario", [
    ScenarioBase.success("User creation success", action, expected_result),
    ScenarioBase.failure("User creation failure", action, expected_exception),
])
async def test_user_creation(test_scenario, processors):
    await test_scenario.test(processors.create_user.wait_for_complete)
```

### Integration Testing
```python
async def test_user_lifecycle(processors, create_user, database_engine):
    # Test complete user lifecycle
    async with create_user(email="test@example.com", name="test", domain_name="default") as user_id:
        # Test operations
        assert user_id is not None
```

### Mock Setup
```python
from unittest.mock import MagicMock

@pytest.fixture
def mock_dependencies():
    return {
        'storage_manager': MagicMock(),
        'valkey_client': MagicMock(),
        'agent_registry': MagicMock(),
    }
```

## Configuration

### Required Dependencies
- Database connection (PostgreSQL)
- Valkey/Redis client for statistics
- Agent registry for session management
- Storage manager for VFolder operations

### Environment Variables
- Database connection settings
- Redis/Valkey connection configuration
- Security settings (TOTP, IP restrictions)

## Best Practices

1. **Always use transactions** for multi-step operations
2. **Validate input data** before processing
3. **Handle exceptions gracefully** with proper error messages
4. **Use soft delete** for user removal unless purging is explicitly required
5. **Monitor performance** for statistics operations
6. **Test all edge cases** including concurrent operations

## Troubleshooting

### Common Issues
- **Permission denied**: Check user roles and domain access
- **Database constraints**: Verify unique constraints (email, username)
- **Resource cleanup**: Ensure proper cleanup of user resources during purging
- **Statistics errors**: Check Valkey/Redis connection and data consistency

### Debugging
- Enable debug logging for detailed operation traces
- Use database query logging for SQL debugging
- Monitor action execution time and success rates
- Check resource usage during bulk operations
