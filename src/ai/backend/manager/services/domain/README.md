# Domain Service

## Service Overview

The Domain Service manages domain resources in Backend.AI. It provides comprehensive functionality to create, modify, delete, and purge domains, as well as manage domain nodes with permissions and scaling group associations. Domains represent organizational units that group users, projects, and resources together.

## Key Features and Capabilities

- **Create Domain**: Define new domains with specific resource limits and permissions
- **Modify Domain**: Update existing domain configurations and resource allocations
- **Delete Domain**: Soft-delete domains while preserving data relationships
- **Purge Domain**: Permanently remove domains and all associated data
- **Domain Node Management**: Create and modify domain nodes with scaling group permissions
- **Role-Based Access Control**: Differentiate between superadmin and regular user operations
- **Resource Management**: Control various domain aspects including:
  - Total resource slots (CPU, memory, GPU)
  - Allowed vfolder hosts and permissions
  - Allowed Docker registries
  - Integration configurations
  - Dotfiles and custom configurations

## Operation Scenarios

### Creating a Domain

When creating a new domain, the service:
1. Accepts domain configuration through `CreateDomainAction`
2. Validates user permissions and role (superadmin vs regular user)
3. Uses `DomainCreator` to specify domain properties
4. Persists the domain through appropriate repository (admin or regular)
5. Returns success/failure status with domain data

### Modifying a Domain

The modification process:
1. Receives modification request via `ModifyDomainAction`
2. Uses `DomainModifier` to specify which fields to update
3. Validates user permissions based on role
4. Retrieves and updates the existing domain
5. Returns updated domain data or error information

### Deleting a Domain (Soft Delete)

The deletion flow:
1. Accepts deletion request with domain name
2. Validates user permissions and role
3. Performs soft deletion (marks as inactive)
4. Preserves data relationships and history
5. Returns success/failure status

### Purging a Domain (Hard Delete)

The purge process:
1. Accepts purge request with domain name
2. Validates superadmin permissions
3. Permanently removes domain and all associated data
4. Cleans up related resources and relationships
5. Returns success/failure status

### Domain Node Operations

Domain nodes provide extended functionality:
- **Create Domain Node**: Creates domain with permissions and scaling group associations
- **Modify Domain Node**: Updates domain node configurations and scaling group memberships
- Supports adding/removing scaling groups
- Validates scaling group permission conflicts

## API Usage Examples

### Creating a Domain

```python
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.types import DomainCreator, UserInfo
from ai.backend.manager.models.user import UserRole
from ai.backend.common.types import ResourceSlot

# Create user info
user_info = UserInfo(
    id=uuid.uuid4(),
    role=UserRole.SUPERADMIN,
    domain_name="default"
)

# Create domain action
action = CreateDomainAction(
    creator=DomainCreator(
        name="development",
        description="Development environment domain",
        is_active=True,
        total_resource_slots=ResourceSlot({"cpu": 100, "mem": "200g", "cuda.device": 4}),
        allowed_vfolder_hosts={"local": ["rw"], "shared": ["ro"]},
        allowed_docker_registries=["registry.example.com", "docker.io"],
        integration_id="dev-integration"
    ),
    user_info=user_info
)

# Execute
result = await domain_service.create_domain(action)
```

### Modifying a Domain

```python
from ai.backend.manager.services.domain.actions.modify_domain import ModifyDomainAction
from ai.backend.manager.services.domain.types import DomainModifier
from ai.backend.manager.types import OptionalState, TriState

# Partial update - only modify description and resource slots
action = ModifyDomainAction(
    domain_name="development",
    modifier=DomainModifier(
        description=TriState.update("Updated development environment"),
        total_resource_slots=TriState.update(ResourceSlot({"cpu": 200, "mem": "400g"})),
        # Other fields remain unchanged
    ),
    user_info=user_info
)

result = await domain_service.modify_domain(action)
```

### Deleting a Domain

```python
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction

action = DeleteDomainAction(
    name="development",
    user_info=user_info
)
result = await domain_service.delete_domain(action)
```

### Purging a Domain

```python
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction

action = PurgeDomainAction(
    name="development",
    user_info=user_info
)
result = await domain_service.purge_domain(action)
```

### Creating a Domain Node

```python
from ai.backend.manager.services.domain.actions.create_domain_node import CreateDomainNodeAction

action = CreateDomainNodeAction(
    creator=DomainCreator(
        name="compute-cluster",
        description="High-performance compute cluster",
        total_resource_slots=ResourceSlot({"cpu": 500, "mem": "1000g", "cuda.device": 16})
    ),
    user_info=user_info,
    scaling_groups={"gpu-cluster", "cpu-cluster"}
)

result = await domain_service.create_domain_node(action)
```

### Modifying Domain Node

```python
from ai.backend.manager.services.domain.actions.modify_domain_node import ModifyDomainNodeAction
from ai.backend.manager.services.domain.types import DomainNodeModifier

action = ModifyDomainNodeAction(
    name="compute-cluster",
    modifier=DomainNodeModifier(
        description=TriState.update("Updated compute cluster configuration"),
        total_resource_slots=TriState.update(ResourceSlot({"cpu": 750, "mem": "1500g"}))
    ),
    user_info=user_info,
    sgroups_to_add={"new-gpu-cluster"},
    sgroups_to_remove={"old-cpu-cluster"}
)

result = await domain_service.modify_domain_node(action)
```

## Integration Points

### Repository Layer

The service integrates with two repository types:

#### DomainRepository (Regular Operations)
- Validated operations with permission checks
- Standard domain CRUD operations
- Scaling group permission management
- Located at: `src/ai/backend/manager/repositories/domain/repository.py`

#### AdminDomainRepository (Superadmin Operations)
- Force operations bypassing some validations
- Administrative domain management
- Enhanced permissions for system administration
- Located at: `src/ai/backend/manager/repositories/domain/admin_repository.py`

### Database Models

Uses `DomainRow` from the models layer with the following key fields:

- **name**: Unique domain identifier (primary key)
- **description**: Optional domain description
- **is_active**: Domain activation status
- **created_at/modified_at**: Timestamp tracking
- **total_resource_slots**: Available compute resources
- **allowed_vfolder_hosts**: Virtual folder host permissions
- **allowed_docker_registries**: Permitted Docker registries
- **dotfiles**: Custom configuration files
- **integration_id**: External integration identifier

### Action System

The service follows the action-based pattern with comprehensive operations:

1. **CreateDomainAction** (src/ai/backend/manager/services/domain/actions/create_domain.py)
   - Uses `DomainCreator` for input validation
   - Returns `CreateDomainActionResult` with domain data and status

2. **ModifyDomainAction** (src/ai/backend/manager/services/domain/actions/modify_domain.py)
   - Accepts `DomainModifier` for partial updates
   - Returns `ModifyDomainActionResult` with updated domain data

3. **DeleteDomainAction** (src/ai/backend/manager/services/domain/actions/delete_domain.py)
   - Performs soft deletion operations
   - Returns `DeleteDomainActionResult` with success status

4. **PurgeDomainAction** (src/ai/backend/manager/services/domain/actions/purge_domain.py)
   - Permanently removes domain data
   - Returns `PurgeDomainActionResult` with purge status

5. **CreateDomainNodeAction** (src/ai/backend/manager/services/domain/actions/create_domain_node.py)
   - Creates domain with scaling group associations
   - Returns `CreateDomainNodeActionResult` with node data

6. **ModifyDomainNodeAction** (src/ai/backend/manager/services/domain/actions/modify_domain_node.py)
   - Updates domain node configurations
   - Manages scaling group memberships
   - Returns `ModifyDomainNodeActionResult` with updated data

## Error Handling

The service implements comprehensive error handling:

### Service Layer
- **Exception Handling**: All operations wrapped in try-catch blocks
- **Success/Failure Results**: Each action returns success status with description
- **Permission Validation**: Role-based access control enforcement
- **Input Validation**: Scaling group conflict detection

### Repository Layer
- **IntegrityError**: Raised for database constraint violations
- **ValidationError**: Raised for permission or data validation failures
- **NotFoundError**: Raised when domain lookup fails
- **Transaction Failures**: Proper rollback on errors

### Domain Node Specific
- **Scaling Group Conflicts**: Validation prevents adding and removing same groups
- **Permission Conflicts**: Ensures consistent scaling group permissions
- **Resource Validation**: Validates resource slot allocations

## Best Practices

1. **Role-Based Operations**: 
   - Use appropriate user roles (superadmin vs regular user)
   - Understand permission implications for each operation type

2. **Resource Management**:
   - Set realistic resource limits based on infrastructure capacity
   - Monitor resource usage across domains
   - Plan for scaling group resource allocation

3. **Domain Lifecycle**:
   - Use soft deletion for operational domains
   - Reserve purge operations for administrative cleanup
   - Maintain audit trails for domain changes

4. **Scaling Group Management**:
   - Validate scaling group associations before modifications
   - Avoid conflicts between add/remove operations
   - Monitor scaling group permissions and usage

5. **Integration Considerations**:
   - Use integration_id for external system mapping
   - Maintain consistent vfolder host permissions
   - Validate Docker registry accessibility

6. **Error Handling**:
   - Always check action result success status
   - Handle IntegrityError for duplicate domain names
   - Implement proper logging for operational debugging

7. **Performance Considerations**:
   - Use repository decorators for monitoring
   - Implement proper transaction boundaries
   - Consider caching for frequently accessed domains

## Testing Guidelines

### Test Coverage Areas

- **Service Layer**: Action processing and error handling
- **Repository Layer**: Database operations and validations
- **Permission Testing**: Role-based access control
- **Integration Testing**: End-to-end domain lifecycle
- **Edge Cases**: Conflict resolution and error scenarios

### Key Test Scenarios

- Domain creation with various configurations
- Partial updates using modifiers
- Soft deletion and purge operations
- Domain node creation with scaling groups
- Permission validation across user roles
- Error handling and rollback scenarios