# Image Service

## Service Overview

The Image Service is a core component of Backend.AI that manages container images throughout their lifecycle. It provides comprehensive functionality for image management, including soft/hard deletion, alias management, metadata scanning, resource limit configuration, and integration with container registries.

## Key Features and Capabilities

### 1. Image Lifecycle Management
- **Soft Delete (Forget)**: Mark images as inactive without removing from database
- **Hard Delete (Purge)**: Completely remove images from database and agents
- **Role-based Access Control**: Different permissions for superadmins vs regular users

### 2. Image Alias Management
- Create human-friendly aliases for complex image names
- Support for multiple aliases per image
- Alias resolution for all image operations
- Prevent circular alias references

### 3. Image Metadata Operations
- Scan and update image metadata from registries
- Modify image properties (name, labels, resource limits)
- Clear custom resource limits
- Support for multi-architecture images

### 4. Registry Integration
- Untag images from container registries
- Support for multiple registry backends
- Authentication handling for private registries

### 5. Agent Integration
- Purge images from agent nodes
- Batch operations for multiple agents
- Error handling for offline agents
- Progress tracking for long-running operations

## Operation Scenarios

### Scenario 1: Removing Unused Images
```python
# 1. Soft delete to mark as inactive
action = ForgetImageAction(
    reference="old-app:v1.0",
    architecture="x86_64",
    client_role=UserRole.SUPERADMIN,
    user_id=admin_id
)
await image_service.forget_image(action)

# 2. Purge from agents
purge_action = PurgeImagesAction(
    keys=[PurgeImagesKey(
        agent_id="agent-1",
        images=[ImageRef(name="old-app:v1.0", architecture="x86_64")]
    )],
    force=True,
    noprune=False
)
await image_service.purge_images(purge_action)

# 3. Hard delete from database
delete_action = PurgeImageByIdAction(
    image_id=image_id,
    client_role=UserRole.SUPERADMIN,
    user_id=admin_id
)
await image_service.purge_image_by_id(delete_action)
```

### Scenario 2: Creating User-Friendly Aliases
```python
# Create alias for complex image name
alias_action = AliasImageAction(
    alias="tensorflow-gpu",
    image_canonical="nvcr.io/nvidia/tensorflow:22.12-tf2-py3",
    architecture="x86_64"
)
await image_service.alias_image(alias_action)

# Users can now reference the image as "tensorflow-gpu"
```

### Scenario 3: Updating Image Resource Limits
```python
# Set custom resource limits
modify_action = ModifyImageAction(
    target="compute-heavy:latest",
    architecture="x86_64",
    modifier=ImageModifier(
        resource_limits={"cpu": "8", "memory": "32G", "gpu": "2"}
    )
)
await image_service.modify_image(modify_action)

# Clear custom limits to use defaults
clear_action = ClearImageCustomResourceLimitAction(
    image_canonical="compute-heavy:latest",
    architecture="x86_64"
)
await image_service.clear_image_custom_resource_limit(clear_action)
```

### Scenario 4: Multi-Agent Image Cleanup
```python
# Purge images from multiple agents in parallel
action = PurgeImagesAction(
    keys=[
        PurgeImagesKey(
            agent_id="agent-1",
            images=[
                ImageRef(name="app:old", architecture="x86_64"),
                ImageRef(name="cache:old", architecture="x86_64")
            ]
        ),
        PurgeImagesKey(
            agent_id="agent-2",
            images=[ImageRef(name="app:old", architecture="x86_64")]
        )
    ],
    force=True,
    noprune=False
)
result = await image_service.purge_images(action)

# Check results
for purged in result.purged_images:
    print(f"Agent {purged.agent_id}: {len(purged.purged_images)} images purged")
for error in result.errors:
    print(f"Error: {error}")
```

## API Usage Examples

### Basic Operations
```python
# Initialize service
image_service = ImageService(
    agent_registry=agent_registry,
    image_repository=image_repository,
    admin_image_repository=admin_image_repository
)

# Forget image (soft delete)
await image_service.forget_image(ForgetImageAction(...))

# Forget by ID
await image_service.forget_image_by_id(ForgetImageByIdAction(...))

# Create alias
await image_service.alias_image(AliasImageAction(...))

# Remove alias
await image_service.dealias_image(DealiasImageAction(...))

# Scan image metadata
await image_service.scan_image(ScanImageAction(...))

# Modify image properties
await image_service.modify_image(ModifyImageAction(...))

# Purge from agents
await image_service.purge_images(PurgeImagesAction(...))

# Hard delete with aliases
await image_service.purge_image_by_id(PurgeImageByIdAction(...))

# Untag from registry
await image_service.untag_image_from_registry(UntagImageFromRegistryAction(...))

# Clear resource limits
await image_service.clear_image_custom_resource_limit(ClearImageCustomResourceLimitAction(...))
```

### Error Handling
```python
try:
    result = await image_service.forget_image(action)
except ImageNotFound:
    # Image doesn't exist or user doesn't have access
    pass
except PermissionDenied:
    # User lacks required permissions
    pass
except Exception as e:
    # Handle other errors
    logger.error(f"Failed to forget image: {e}")
```

## Integration Points

### 1. Repository Layer
- `ImageRepository`: Handles user-scoped operations with permission checks
- `AdminImageRepository`: Handles admin operations without permission checks

### 2. Agent Registry
- Communicates with agent nodes for image operations
- Handles distributed image purging
- Manages agent availability and error recovery

### 3. Container Registry
- Integrates with Docker Hub, private registries, etc.
- Handles authentication and authorization
- Manages image tags and manifests

### 4. Database Models
- `ImageRow`: Core image metadata storage
- `ImageAliasRow`: Alias to image mappings
- Supports transactions and consistency

## Testing Guidelines

### Unit Tests
Located in `tests/manager/services/image/test_image_service.py`
- Mock all dependencies (repositories, agent registry)
- Test each service method independently
- Cover success and error cases
- Verify permission checks

### Integration Tests
Located in `tests/manager/integration/services/image/test_image_service.py`
- Use real database connections
- Test complete workflows
- Verify data persistence
- Test transaction boundaries

### Repository Tests
Located in `tests/manager/repositories/image/test_image_repository.py`
- Test data access layer
- Verify SQL queries
- Test permission validations
- Cover edge cases

### Test Patterns
```python
# Use fixtures for common setup
@pytest.fixture
async def create_test_image(database_engine):
    @asynccontextmanager
    async def _create_image(**kwargs):
        # Create and yield test image
        # Cleanup after test
    return _create_image

# Test with proper assertions
async def test_forget_image_success(image_service, create_test_image):
    async with create_test_image() as image:
        result = await image_service.forget_image(action)
        assert result.image.id == image.id
        assert not result.image.is_active
```

## Best Practices

1. **Always validate permissions** before performing operations
2. **Use transactions** for multi-step operations
3. **Handle partial failures** gracefully in batch operations
4. **Log important operations** for audit trails
5. **Validate input** early to fail fast
6. **Use appropriate exceptions** for different error cases
7. **Document breaking changes** in service methods
8. **Maintain backwards compatibility** when possible

## Performance Considerations

1. **Batch operations** when dealing with multiple images
2. **Use async/await** properly to avoid blocking
3. **Implement pagination** for large result sets
4. **Cache frequently accessed** image metadata
5. **Optimize database queries** with proper indexes
6. **Handle timeouts** for long-running agent operations

## Security Considerations

1. **Validate user permissions** for all operations
2. **Sanitize input** to prevent injection attacks
3. **Use secure communication** with agents
4. **Audit sensitive operations** like deletion
5. **Implement rate limiting** for expensive operations
6. **Validate image sources** before scanning