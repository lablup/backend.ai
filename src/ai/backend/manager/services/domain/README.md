# Domain Service

## Service Overview

The Domain Service manages domain resources in Backend.AI. It creates, modifies, deletes and purges domains. Domains are organizational units that group users, projects and resources together.

## Key Features and Capabilities

- **Create Domain**: Define new domains with specific resource limits and permissions
- **Modify Domain**: Update existing domain configurations and resource allocations
- **Delete Domain**: Soft-delete domains while preserving data relationships
- **Purge Domain**: Remove domains and all associated data permanently
- **RBAC**: Distinguish between superadmin and regular user operations
- **Resource Management**: Control various domain aspects including:
  - Total resource slots (CPU, memory, GPU)
  - Allowed vfolder hosts and permissions
  - Allowed container registries
  - Integration configurations
  - Dotfiles and custom configurations

## Operation Scenarios

### Creating a Domain

When creating a new domain, the service:
1. Accepts domain configuration through `CreateDomainAction`
2. Validates user permissions and role (superadmin or regular user)
3. Uses `DomainCreator` to specify domain properties
4. Persists the domain through the repository
5. Returns success or failure status with domain data

### Modifying a Domain

The modification process:
1. Receives modification request via `ModifyDomainAction`
2. Uses `DomainModifier` to specify which fields to update
3. Validates user permissions based on role
4. Gets and updates the existing domain
5. Returns updated domain data or error information

### Deleting a Domain (Soft Delete)

The deletion flow:
1. Accepts deletion request with domain name
2. Validates user permissions and role
3. Performs soft deletion (marks as inactive)
4. Preserves data relationships and history
5. Returns success or failure status

### Purging a Domain (Hard Delete)

The purge process:
1. Accepts purge request with domain name
2. Validates superadmin permissions
3. Removes the domain and all associated data permanently
4. Cleans up related resources and relationships
5. Returns success or failure status

## API Usage Examples

### Creating a Domain

```python
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.common.types import ResourceSlot

action = CreateDomainAction(
    creator=DomainCreator(
        name="development",
        description="Development environment domain",
        is_active=True,
        total_resource_slots=ResourceSlot({"cpu": 100, "mem": "200g", "cuda.device": 4}),
        allowed_vfolder_hosts={"local": ["rw"], "shared": ["ro"]},
        allowed_docker_registries=["registry.example.com", "docker.io"],
        integration_name="dev-integration",
    ),
)

result = await processors.domain.create.run(action)
```

The action writes the domain row, its preset roles and the model-store project the domain is registered with, in one transaction.

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

## Integration Points

### Repository Layer

The service integrates with the repository:

#### DomainRepository
- All domain create, get, update and delete operations
- Resource group permission management
- Located at: `src/ai/backend/manager/repositories/domain/repository.py`

### Database Models

Uses `DomainRow` from the models layer with the following key fields:

- **name**: Unique domain identifier (primary key)
- **description**: Optional domain description
- **is_active**: Domain activation status
- **created_at/updated_at**: Timestamp tracking
- **total_resource_slots**: Available compute resources
- **allowed_vfolder_hosts**: vfolder host permissions
- **allowed_docker_registries**: Permitted container registries
- **dotfiles**: Custom configuration files
- **integration_id**: External integration identifier

### Action System

The service follows the action-based pattern with these operations:

1. **CreateDomainAction** (src/ai/backend/manager/services/domain/actions/create_domain.py)
   - Carries `DomainCreator`; wired to the generic role-managed create
   - Returns `CreatedEntityOpsResult[DomainData]`

2. **ModifyDomainAction** (src/ai/backend/manager/services/domain/actions/modify_domain.py)
   - Accepts `DomainModifier` for partial updates
   - Returns `ModifyDomainActionResult` with updated domain data

3. **DeleteDomainAction** (src/ai/backend/manager/services/domain/actions/delete_domain.py)
   - Performs soft deletion operations
   - Returns `DeleteDomainActionResult` with success status

4. **PurgeDomainAction** (src/ai/backend/manager/services/domain/actions/purge_domain.py)
   - Removes domain data permanently
   - Returns `PurgeDomainActionResult` with purge status

## Error Handling

The service implements error handling at each layer:

### Service Layer
- **Exception Handling**: All operations wrapped in try-catch blocks
- **Success or Failure Results**: Each action returns success status with description
- **Permission Validation**: RBAC enforcement

### Repository Layer
- **IntegrityError**: Raised for database constraint violations
- **ValidationError**: Raised for permission or data validation failures
- **NotFoundError**: Raised when a domain lookup fails
- **Transaction Failures**: Rollback on errors

## Best Practices

1. **Role-Based Operations**: 
   - Use appropriate user roles (superadmin or regular user)
   - Understand permission implications for each operation type

2. **Resource Management**:
   - Set realistic resource limits based on infrastructure capacity
   - Monitor resource usage across domains
   - Plan resource allocation across resource groups

3. **Domain Lifecycle**:
   - Use soft deletion for operational domains
   - Reserve purge operations for administrative cleanup
   - Maintain audit trails for domain changes

4. **Resource Group Management**:
   - Validate resource group associations before modifications
   - Avoid conflicts between add and remove operations
   - Monitor resource group permissions and usage

5. **Integration Considerations**:
   - Use integration_id for external system mapping
   - Maintain consistent vfolder host permissions
   - Validate container registry accessibility

6. **Error Handling**:
   - Always check action result success status
   - Handle IntegrityError for duplicate domain names
   - Implement logging for operational debugging

7. **Performance Considerations**:
   - Use repository decorators for monitoring
   - Implement transaction boundaries
   - Consider caching for frequently accessed domains

## Testing Guidelines

### Test Coverage Areas

- **Service Layer**: Action processing and error handling
- **Repository Layer**: Database operations and validations
- **Permission Testing**: RBAC
- **Integration Testing**: End-to-end domain lifecycle
- **Edge Cases**: Conflict resolution and error scenarios

### Key Test Scenarios

- Domain creation with various configurations
- Partial updates using modifiers
- Soft deletion and purge operations
- Permission validation across user roles
- Error handling and rollback scenarios