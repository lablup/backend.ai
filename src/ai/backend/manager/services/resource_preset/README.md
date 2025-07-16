# Resource Preset Service

## Service Overview

The Resource Preset Service manages computing resource allocation templates in Backend.AI. It provides pre-defined combinations of CPU, memory, GPU, and other resources that users can easily select when creating computing sessions. This service simplifies resource allocation by offering standardized resource configurations while supporting custom resource types for specialized hardware.

## Key Features and Capabilities

### 1. Preset Management
- **Create Preset**: Define new resource allocation templates with specific CPU, memory, GPU, and custom resource combinations
- **Modify Preset**: Update existing presets including resource slots, names, and shared memory configurations
- **Delete Preset**: Remove unused or obsolete presets from the system
- **List Presets**: Retrieve available presets globally or filtered by scaling group

### 2. Resource Validation
- Enforces intrinsic resource requirements (CPU and memory must always be specified)
- Supports custom resource types (NPU, TPU, etc.) for specialized hardware
- Validates resource slot specifications during creation and modification

### 3. Scaling Group Support
- Global presets available across all scaling groups
- Scaling group-specific presets for cluster-specific configurations
- Namespace isolation allowing same preset names in different scaling groups

### 4. Resource Availability Checking
- Real-time validation of preset allocatability based on current resource usage
- Multi-level resource limit checking (keypair, group, domain)
- Per-agent resource availability verification
- Scaling group resource visibility control

## Operation Scenarios

### Creating a Resource Preset

```python
# Create a CPU-only preset
action = CreateResourcePresetAction(
    creator=ResourcePresetCreator(
        name="cpu-small",
        resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
        shared_memory="1G",
        scaling_group_name=None  # Global preset
    )
)
result = await resource_preset_service.create_preset(action)
```

### Modifying an Existing Preset

```python
# Update resource allocation
action = ModifyResourcePresetAction(
    name="cpu-small",
    modifier=ResourcePresetModifier(
        resource_slots=OptionalState(
            ResourceSlot({"cpu": "4", "memory": "8G"}),
            has_value=True
        )
    )
)
result = await resource_preset_service.modify_preset(action)
```

### Checking Resource Availability

```python
# Check which presets can be allocated
action = CheckResourcePresetsAction(
    access_key="user-key",
    resource_policy={"total_resource_slots": {"cpu": "100", "memory": "100G"}},
    domain_name="default",
    group="research-team",
    user_id=user_uuid,
    scaling_group="gpu-cluster"
)
result = await resource_preset_service.check_presets(action)

# Result includes allocatability status for each preset
for preset in result.presets:
    print(f"{preset['name']}: {'Available' if preset['allocatable'] else 'Unavailable'}")
```

## API Usage Examples

### Service Initialization

```python
from ai.backend.manager.services.resource_preset.service import ResourcePresetService

resource_preset_service = ResourcePresetService(
    db=db_engine,
    agent_registry=agent_registry,
    config_provider=config_provider,
    resource_preset_repository=resource_preset_repository
)
```

### Creating Specialized Presets

```python
# GPU preset for machine learning workloads
gpu_preset = CreateResourcePresetAction(
    creator=ResourcePresetCreator(
        name="ml-training",
        resource_slots=ResourceSlot({
            "cpu": "8",
            "memory": "32G",
            "gpu": "2",
            "gpu_memory": "16G"
        }),
        shared_memory="4G",
        scaling_group_name="gpu-cluster"
    )
)

# Custom hardware preset
custom_preset = CreateResourcePresetAction(
    creator=ResourcePresetCreator(
        name="quantum-compute",
        resource_slots=ResourceSlot({
            "cpu": "4",
            "memory": "16G",
            "qpu": "1"  # Custom quantum processing unit
        }),
        shared_memory="2G",
        scaling_group_name="quantum-cluster"
    )
)
```

## Integration Points

### 1. Repository Layer
- `ResourcePresetRepository`: Handles database operations with transaction safety
- Provides CRUD operations with proper error handling
- Supports both UUID and name-based lookups

### 2. Agent Registry
- Queries real-time resource occupancy across keypairs, groups, and domains
- Provides agent resource availability for allocatability checks

### 3. Configuration Provider
- Manages resource slot definitions and types
- Controls group resource visibility settings
- Provides system-wide resource configuration

### 4. Database Models
- `ResourcePresetRow`: Core preset data model
- Supports resource slot normalization and validation
- Handles scaling group associations

## Testing Guidelines

### Unit Testing

The service includes comprehensive test coverage for all operations:

1. **Create Preset Tests**
   - Valid preset creation scenarios
   - Intrinsic slot validation
   - Duplicate name handling
   - Scaling group namespace isolation

2. **Modify Preset Tests**
   - Resource slot updates
   - Name changes
   - Partial updates
   - Error handling for invalid modifications

3. **Delete Preset Tests**
   - Normal deletion
   - In-use preset deletion (presets are templates, deletion doesn't affect running sessions)
   - UUID and name-based deletion

4. **List Preset Tests**
   - Global preset listing
   - Scaling group filtering
   - Resource slot normalization

5. **Check Preset Tests**
   - Resource availability scenarios
   - Multi-level limit checking
   - Group visibility settings
   - Error cases

### Integration Testing

When testing integration with other services:

1. Ensure database fixtures include necessary resource policies
2. Mock agent registry responses appropriately
3. Test scaling group associations
4. Verify resource slot calculations across different limit levels

### Performance Considerations

- List operations stream results to handle large preset collections
- Check operations optimize queries to minimize database round trips
- Resource calculations use efficient slot arithmetic operations

## Error Handling

The service handles various error conditions:

- `InvalidAPIParameters`: Missing required parameters or invalid resource specifications
- `ResourcePresetConflict`: Duplicate preset names within the same namespace
- `ObjectNotFound`: Attempting to modify or delete non-existent presets
- Database integrity constraints for data consistency

## Future Enhancements

Potential areas for service enhancement:

1. **Preset Templates**: Hierarchical presets with inheritance
2. **Dynamic Presets**: Auto-scaling based on workload patterns
3. **Usage Analytics**: Track preset popularity and resource utilization
4. **Preset Recommendations**: ML-based preset suggestions based on workload type
5. **Resource Quotas**: Time-based or usage-based preset limitations