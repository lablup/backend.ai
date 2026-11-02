# SchedulingController

← [Back to Sokovan](../README.md#sokovan-component-documentation) | [Manager](../../README.md#manager-architecture-documentation) | [Architecture Overview](../../../README.md#manager)

## Overview

SchedulingController handles pre-validation and preparation of session creation requests. It validates the request and prepares the data the Scheduler needs before the Scheduler schedules sessions.

**Key Responsibilities:**
- **Request Validation**: Blocks invalid requests before they reach the scheduling stage
- **Data Preparation**: Prepares the data needed for scheduling and transforms it into the appropriate format
- **Resource Calculation**: Calculates the amount of resources that sessions actually require
- **Resource Group Selection**: Determines the resource group most suitable to execute the session
- **Configuration Validation**: Verifies the validity of multi-kernel session and volume mount configurations

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SchedulingController                             │
│            - Orchestrates request validation/prep                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┬─────────────────┐
           │                   │                   │                 │
           ▼                   ▼                   ▼                 ▼
┌────────────────────┐ ┌───────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│                    │ │                   │ │                  │ │                  │
│    Validators      │ │    Preparers      │ │   Calculators    │ │    Resolvers     │
│                    │ │                   │ │                  │ │                  │
└────────────────────┘ └───────────────────┘ └──────────────────┘ └──────────────────┘
```

## Dependencies

SchedulingController depends on the following infrastructure components:

**PostgreSQL**: Queries resource group, domain and user information

**Valkey**: Caches resource constraints

**etcd**: Shares global configuration

## Data Flow

SchedulingController processes the following data through validation and preparation:

**Input**: The user's session creation request (image, resources, cluster size, mounts and so on)

**Validation Stage**: Verifies request validity and validates user permissions and resource constraints

**Preparation Stage**: Generates internal data, prepares cluster and mount configurations, and calculates resource requirements

**Output**: Delivers validated and prepared session data to the Scheduler

## Major Components

### SchedulingController

SchedulingController is the main controller that orchestrates the validation and preparation process for session creation requests.

**Key Tasks:**
- **Execute Validation Pipeline**: Verifies request validity through multiple validation rules
- **Execute Preparation Pipeline**: Generates the data needed for scheduling with various preparation rules
- **Resource Calculation**: Calculates actual resource requirements through the resource calculator
- **Resource Group Determination**: Selects the optimal resource group through the resource group resolver
- **Data Return**: Delivers data with all validation and preparation completed to the Scheduler

**Key Methods:**

#### `prepare_session()`
Performs all preparation tasks before session creation.

**Processing Flow:**
```
1. Request validation (Validators)
   ├─ Cluster size validation
   ├─ Mount path validation
   └─ Scaling group filtering
   ↓
2. Data preparation (Preparers)
   ├─ Internal data preparation
   ├─ Cluster configuration preparation
   └─ Mount configuration preparation
   ↓
3. Resource calculation (Calculators)
   └─ Calculate required resources
   ↓
4. Scaling group resolution (Resolvers)
   └─ Select suitable scaling group
   ↓
5. Return prepared data
```

**Return Value:**
```python
PreparedSessionData(
    validated_request: ValidatedRequest,
    internal_data: InternalData,
    cluster_config: ClusterConfig,
    mount_config: MountConfig,
    resource_requirements: ResourceRequirements,
    scaling_group: ScalingGroup
)
```

#### `validate_session()`
Validates the session creation request.

**Processing Flow:**
```
1. Execute each validation rule
   ├─ ClusterValidationRule
   ├─ MountValidationRule
   └─ ScalingGroupFilteringRule
   ↓
2. Raise exception on validation failure
   └─ ValidationError with details
   ↓
3. Return ValidatedRequest on validation success
```

## Validators

Validator verifies whether session creation requests satisfy system constraints and policies.

### Basic Structure

All validation rules inherit from the ValidationRule abstract class and must implement the `validate()` method that executes the validation logic. If validation fails, they raise a ValidationError exception that stops the scheduling process immediately.

SessionValidator is a container that manages multiple ValidationRules, executes the registered rules sequentially, and stops processing immediately if any rule fails.

### Key Validation Rules

#### ClusterValidationRule

ClusterValidationRule validates the validity of the multi-kernel session configuration.

**Validation Items:**
- Verify cluster size is 1 or greater
- Validate that the requested container image supports cluster mode
- Confirm that the selected cluster mode is supported by the system

**Examples:**
```python
# Failure case
{
    "cluster_size": 0  # Error: cluster size must be 1 or greater
}

# Success case
{
    "cluster_size": 3,
    "cluster_mode": "multi-container"
}
```

#### MountValidationRule

MountValidationRule validates the validity of volume mount paths and configuration.

**Validation Items:**
- Validate that the mount path is in the correct format
- Detect attempts to mount duplicate paths
- Verify that the requested read/write permissions are allowed
- Validate that the volume is actually mountable

**Examples:**
```python
# Failure case
{
    "mounts": [
        {"path": "/data", "vfolder": "folder1"},
        {"path": "/data", "vfolder": "folder2"}  # Error: duplicate path
    ]
}

# Success case
{
    "mounts": [
        {"path": "/data", "vfolder": "folder1", "mode": "rw"},
        {"path": "/model", "vfolder": "folder2", "mode": "ro"}
    ]
}
```

#### ScalingGroupFilteringRule

ScalingGroupFilteringRule filters the resource groups that can execute the session.

**Validation Items:**
- Verify that the resource group supports the requested resource types (CPU, GPU and so on)
- Validate access permissions for the user's domain and resource group
- Confirm resource slot compatibility

**Filtering Criteria:**
- Whether the resource group has sufficient available resources
- Whether it supports the requested container image
- Whether the user has permission to access the resource group's network and storage
- Whether the resource slot types are compatible

**Examples:**
```python
# Request
{
    "resources": {
        "cpu": "4",
        "memory": "16g",
        "nvidia.com/gpu": "2"
    }
}

# Filtering result
[
    ScalingGroup(name="gpu-group-1", ...),  # GPU supported
    ScalingGroup(name="gpu-group-2", ...)   # GPU supported
]
# cpu-only-group excluded (GPU not supported)
```

## Preparers

Preparer prepares and transforms the data needed for scheduling. It processes validated requests into a format usable for actual scheduling.

### Basic Structure

All preparation rules inherit from the PreparationRule abstract class and implement the `prepare()` method that executes the preparation logic. This method transforms the input data or augments it with the necessary information.

SessionPreparer is a container that manages multiple PreparationRules, executes the registered rules sequentially, and passes the output of each rule as the input of the next rule in a pipeline.

### Key Preparation Rules

#### InternalDataPreparer

InternalDataPreparer prepares the data needed for internal system processing.

**Preparation Items:**
- Generate a unique session ID
- Set timestamps such as the session creation time
- Apply default values for unspecified user settings
- Add the metadata needed for tracking or analysis

**Examples:**
```python
# Input
{
    "image": "python:3.11",
    "resources": {...}
}

# Output
{
    "session_id": "sess-abc123",
    "image": "python:3.11",
    "resources": {...},
    "created_at": "2024-01-15T10:30:00Z",
    "metadata": {
        "user_id": "user123",
        "project_id": "proj456"
    }
}
```

#### ClusterPreparer

ClusterPreparer prepares the multi-kernel session configuration.

**Preparation Items:**
- Configure the appropriate cluster mode according to the cluster size
- Configure network settings for inter-node communication
- Generate an SSH key pair if needed
- Prepare the dedicated network configuration of the multi-kernel session

**Cluster Modes:**
- `single-node`: Default mode running as single container
- `multi-container`: Run multiple containers on one agent
- `multi-node`: Distribute containers across multiple agents

**Examples:**
```python
# Input
{
    "cluster_size": 3
}

# Output
{
    "cluster_size": 3,
    "cluster_mode": "multi-node",
    "cluster_config": {
        "ssh_keypair": "generated_keypair",
        "node_roles": ["main", "worker", "worker"],
        "network_config": {...}
    }
}
```

#### MountPreparer

MountPreparer prepares the volume mount configuration.

**Preparation Items:**
- Normalize user-specified mount paths to system standard paths
- Create mappings between vfolders and container paths
- Set read/write permissions explicitly
- Add mount options such as bind mount

**Examples:**
```python
# Input
{
    "mounts": [
        {"path": "/data", "vfolder": "my-data"}
    ]
}

# Output
{
    "mounts": [
        {
            "path": "/home/work/data",  # Normalized path
            "vfolder": "my-data",
            "vfolder_id": "vf123",
            "mode": "rw",
            "mount_options": ["bind", "rw"]
        }
    ]
}
```

## Calculators

Calculator accurately calculates the resource requirements that sessions actually need.

### ResourceCalculator

ResourceCalculator is the calculator that computes session resource requirements.

**Calculation Items:**
- Start from the basic resource amount requested by the user
- Calculate the actual requirement considering system overhead
- Apply the multiplier for the node count according to the cluster mode
- Convert resource slots to the system standard format

**Calculation Logic:**
```python
# Single container
total_resources = requested_resources + overhead

# Multiple containers/nodes
total_resources = (requested_resources + overhead) * cluster_size
```

**Examples:**
```python
# Input
{
    "resources": {
        "cpu": "2",
        "memory": "8g",
        "nvidia.com/gpu": "1"
    },
    "cluster_size": 3
}

# Calculation
base_cpu = 2
base_memory = 8 * 1024 * 1024 * 1024  # Convert to bytes
base_gpu = 1

# Add overhead (e.g., 10%)
cpu_with_overhead = base_cpu * 1.1 = 2.2
memory_with_overhead = base_memory * 1.1
gpu_with_overhead = base_gpu  # No GPU overhead

# Apply cluster multiplier
total_cpu = cpu_with_overhead * 3 = 6.6
total_memory = memory_with_overhead * 3
total_gpu = gpu_with_overhead * 3 = 3

# Output
{
    "per_container": {
        "cpu": "2.2",
        "memory": "8.8g",
        "nvidia.com/gpu": "1"
    },
    "total": {
        "cpu": "6.6",
        "memory": "26.4g",
        "nvidia.com/gpu": "3"
    }
}
```

## Resolvers

Resolver makes optimal choices among multiple options or solves complex decision problems.

### ScalingGroupResolver

ScalingGroupResolver validates whether the selected resource group is usable in the filtered resource group list.

**Resolution Process:**
```
1. Receive filtered scaling group list
   ↓
2. Check availability of selected scaling group
   ├─ Group existence
   ├─ Group activation state
   └─ Group access permission
   ↓
3. Return scaling group on validation success
   ↓
4. Raise exception on validation failure
```

**Examples:**
```python
# Input: Filtered groups and selected group name
filtered_groups = ["gpu-1", "gpu-2", "cpu-1"]
selected_group = "gpu-2"

# Validation
- ✓ "gpu-2" exists in filtered groups
- ✓ "gpu-2" is in active state
- ✓ User has "gpu-2" access permission

# Return
ScalingGroup(name="gpu-2", ...)
```

## Complete Processing Flow

### Session Creation Request → Scheduling Preparation

```
1. API: Receive session creation request
   {
       "image": "python:3.11",
       "resources": {"cpu": "2", "memory": "8g"},
       "cluster_size": 1,
       "mounts": [...]
   }
   ↓
2. SchedulingController.prepare_session()
   ↓
3. Execute Validators
   ├─ ClusterValidationRule
   │   └─ ✓ cluster_size >= 1
   ├─ MountValidationRule
   │   └─ ✓ Mount paths valid
   └─ ScalingGroupFilteringRule
       └─ [gpu-1, cpu-1, hybrid-1] → [cpu-1]
   ↓
4. Execute Preparers
   ├─ InternalDataPreparer
   │   └─ Generate session_id, timestamps
   ├─ ClusterPreparer
   │   └─ Configure cluster_config
   └─ MountPreparer
       └─ Normalize mount_config
   ↓
5. Execute Calculators
   └─ ResourceCalculator
       └─ Calculate total_resources
   ↓
6. Execute Resolvers
   └─ ScalingGroupResolver
       └─ Select optimal scaling group: cpu-1
   ↓
7. Return prepared data
   {
       "session_id": "sess-abc123",
       "validated_request": {...},
       "internal_data": {...},
       "cluster_config": {...},
       "mount_config": {...},
       "resource_requirements": {...},
       "scaling_group": ScalingGroup(name="cpu-1", ...)
   }
   ↓
8. Scheduler: Begin scheduling
```

## Pipeline Pattern

SchedulingController uses the pipeline pattern:

```python
class Pipeline:
    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def execute(self, data):
        result = data
        for rule in self.rules:
            result = rule.process(result)
        return result

# Usage
validation_pipeline = Pipeline()
validation_pipeline.add_rule(ClusterValidationRule())
validation_pipeline.add_rule(MountValidationRule())
validation_pipeline.add_rule(ScalingGroupFilteringRule())

validated_data = validation_pipeline.execute(request_data)
```

The advantages of the pipeline pattern are: the processing order is clear, which makes the flow easy to understand; rules can be added or removed dynamically, which provides excellent extensibility; each stage operates independently with low coupling; and individual rules can be tested independently, which makes testing easy.

## Error Handling

### ValidationError

ValidationError is the exception raised when a request is invalid during the validation stage. This exception includes which validation rule failed, the specific error message, the name and value of the incorrect fields, and suggestions for resolving the problem when possible.

**Examples:**
```python
ValidationError(
    rule="ClusterValidationRule",
    message="Cluster size must be at least 1",
    field="cluster_size",
    value=0,
    suggestion="Set cluster_size to 1 or more"
)
```

### PreparationError

PreparationError is the exception raised when data transformation or generation fails during the preparation stage. It includes which preparer failed, the specific cause of the error, and the data being prepared.

### CalculationError

CalculationError is the exception raised when an error occurs during resource calculation. It includes the cause of the calculation failure, the input data used for the calculation, and the expected value range.

### ResolutionError

ResolutionError is the exception raised when no suitable option is found. For example, it is raised when no resource group satisfies the requirements of the session. This exception includes the requirements of the session, a list of the reviewed options, and the reason each option is unsuitable.

## Configuration and Extension

### Adding New Validation Rule

```python
class CustomValidationRule(ValidationRule):
    def validate(self, data: dict) -> dict:
        # Validation logic
        if not self._is_valid(data):
            raise ValidationError("Invalid data")
        return data

# Registration
controller = SchedulingController()
controller.add_validation_rule(CustomValidationRule())
```

### Adding New Preparation Rule

```python
class CustomPreparationRule(PreparationRule):
    def prepare(self, data: dict) -> dict:
        # Preparation logic
        prepared_data = self._prepare(data)
        return prepared_data

# Registration
controller.add_preparation_rule(CustomPreparationRule())
```

### Changing Rule Order

When the rule execution order is important, the order can be specified explicitly:

```python
controller.set_validation_order([
    ClusterValidationRule,
    MountValidationRule,
    ScalingGroupFilteringRule
])
```

## Performance Considerations

### Validation Optimization

To optimize the performance of the validation stage, use a Fast Fail strategy that stops immediately at the first validation failure, execute rules without interdependencies in parallel, and cache and reuse repeated validation results for identical requests.

### Data Preparation Optimization

The data preparation process uses Lazy Evaluation to perform calculations only when they are actually needed, maximizes the reuse of results generated in previous stages, and improves efficiency by batching multiple session creation requests for processing at once.

### Resource Calculation Optimization

Resource calculation caches and reuses calculation results for identical inputs, and achieves an appropriate balance between accuracy and speed by using approximate calculation instead of exact calculation depending on the situation.

## Monitoring and Debugging

### Metrics

To monitor system state, track the validation success and failure counts, the failure frequency per validation rule, the time spent in the preparation stage, the time taken for resource calculation, and the resource group selection success rate.

## Troubleshooting

### 1. Repeated Validation Failures

**Symptoms**:
- Session creation requests continuously fail at the validation stage

**Causes**:
- Incorrect request data
- System constraint violations

**Diagnosis**:
- **Check Error Message**: Review the error message returned on session creation failure and the failed rule
- **Request Data**: Validate the cluster size, resource requests, mount paths and so on
- **Constraints**: Check the resource quotas and concurrent session count limits

**Resolution**:
1. Fix the request data format and values
2. Check and adjust the resource quotas
3. Review the system constraints

### 2. Resource Group Selection Failure

**Symptoms**:
- An error reporting that no suitable resource group was found

**Causes**:
- No resource group provides the requested resources
- Insufficient resource group permissions

**Diagnosis**:
- **Available Resource Groups**: Check the list of resource groups accessible to the user
- **Resource Requirements**: Verify which resource groups can provide the requested GPU, memory and so on
- **Permission Settings**: Check the resource group access permissions per domain and project

**Resolution**:
1. Adjust the resource requirements
2. Check and adjust the user permissions
3. Validate the resource group configuration

### 3. Error in Preparation Stage

**Symptoms**:
- Session creation fails in the preparation stage

**Causes**:
- Volume mount validation failure
- Cluster network configuration errors

**Diagnosis**:
- **Error Message**: Identify which preparation stage failed
- **Mount Configuration**: Check the vfolder existence and permissions
- **External Services**: Check the status of the Storage and Network services

**Resolution**:
1. Verify the mount paths and vfolder permissions
2. Check the external service status
3. Review the cluster network configuration

### 4. Resource Calculation Error

**Symptoms**:
- Calculated resources differ from the expected values

**Causes**:
- Unit conversion errors
- Multiplier calculation errors according to the cluster size

**Diagnosis**:
- **Requested Resources**: Check the input resource values and units
- **Cluster Size**: Verify the cluster mode and node count
- **Calculation Result**: Check the final calculated total resources

**Resolution**:
1. Verify the resource units (GB vs GiB and so on)
2. Validate the cluster size
3. Adjust the resource request values if needed

## Parent Document
- [Sokovan Overall Architecture](../README.md)

## Related documents
- [Scheduler Architecture](../scheduler/README.md)
- [Deployment Architecture](../deployment/README.md)
