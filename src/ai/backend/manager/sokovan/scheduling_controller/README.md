# SchedulingController

← [Back to Sokovan](../README.md#sokovan-component-documentation) | [Manager](../../README.md#manager-architecture-documentation) | [Architecture Overview](../../../README.md#manager)

## Overview

SchedulingController is the component responsible for pre-validation and preparation of session creation requests, validating request validity and preparing necessary data before the Scheduler schedules sessions.

**Key Responsibilities:**
- **Request Validation**: Proactively blocks invalid requests from reaching the scheduling stage
- **Data Preparation**: Prepares various data needed for scheduling and transforms to appropriate format
- **Resource Calculation**: Accurately calculates the amount of resources that sessions actually require
- **Scaling Group Selection**: Determines the most suitable scaling group to execute the session
- **Configuration Validation**: Verifies the validity of cluster session and volume mount configurations

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

**PostgreSQL**: Queries scaling group, domain, and user information

**Redis (Valkey)**: Caches resource constraints

**etcd**: Shares global configuration

## Data Flow

SchedulingController processes the following data through validation and preparation:

**Input**: User's session creation request (image, resources, cluster size, mounts, etc.)

**Validation Stage**: Verifies request validity, validates user permissions and resource constraints

**Preparation Stage**: Generates internal data, prepares cluster and mount configurations, calculates resource requirements

**Output**: Delivers validated and prepared session data to Scheduler

## Major Components

### SchedulingController

SchedulingController is the main controller that orchestrates the validation and preparation process for session creation requests.

**Key Tasks:**
- **Execute Validation Pipeline**: Verifies request validity through multiple validation rules
- **Execute Preparation Pipeline**: Generates scheduling-needed data with various preparation rules
- **Resource Calculation**: Calculates actual resource requirements through resource calculator
- **Scaling Group Determination**: Selects optimal group through scaling group resolver
- **Data Return**: Delivers data with all validation and preparation completed to Scheduler

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
Validates session creation request.

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

Validator is the component that verifies whether session creation requests satisfy system constraints and policies.

### Basic Structure

All validation rules inherit from the ValidationRule abstract class and must implement the `validate()` method that executes validation logic. If validation fails, they raise a ValidationError exception to immediately stop the scheduling process.

SessionValidator is a container managing multiple ValidationRules, executing registered rules sequentially and stopping processing immediately if any rule fails.

### Key Validation Rules

#### ClusterValidationRule

ClusterValidationRule validates the validity of cluster session configuration.

**Validation Items:**
- Verify cluster size is 1 or greater
- Validate requested container image supports cluster mode
- Confirm selected cluster mode is supported by system

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
- Validate mount path is in correct format
- Detect attempts to mount duplicate paths
- Verify requested read/write permissions are allowable
- Validate volume is actually mountable

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

ScalingGroupFilteringRule filters suitable scaling groups that can execute the session.

**Validation Items:**
- Verify group supports requested resource types (CPU, GPU, etc.)
- Validate access permissions for user's domain and group
- Confirm resource slot compatibility

**Filtering Criteria:**
- Whether scaling group has sufficient available resources
- Whether it supports requested container image
- Whether user has permission to access group's network and storage
- Whether resource slot types are compatible

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

Preparer is the component that prepares and transforms data needed for scheduling. It processes validated requests into format usable for actual scheduling.

### Basic Structure

All preparation rules inherit from the PreparationRule abstract class and implement the `prepare()` method that executes preparation logic. This method transforms input data or augments it by adding necessary information.

SessionPreparer is a container managing multiple PreparationRules, executing registered rules sequentially and passing the output of previous rules as input to next rules in a pipeline fashion.

### Key Preparation Rules

#### InternalDataPreparer

InternalDataPreparer prepares data needed for internal system processing.

**Preparation Items:**
- Generate unique session ID
- Set timestamps such as session creation time
- Apply default values for unspecified user settings
- Add metadata needed for tracking or analysis

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

ClusterPreparer prepares cluster session configuration.

**Preparation Items:**
- Configure appropriate cluster mode according to cluster size
- Configure network settings for inter-node communication
- Generate SSH key pair if needed
- Prepare cluster-dedicated network configuration

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

MountPreparer prepares volume mount configuration.

**Preparation Items:**
- Normalize user-specified mount paths to system standard paths
- Create mappings between virtual folders and container paths
- Explicitly set read/write permissions
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

Calculator is the component that accurately calculates the resource requirements that sessions actually need.

### ResourceCalculator

ResourceCalculator is the calculator that computes session resource requirements.

**Calculation Items:**
- Start from basic resource amount requested by user
- Calculate actual requirement considering system overhead
- Apply multiplier for node count according to cluster mode
- Convert resource slots to system standard format

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

Resolver is the component that makes optimal choices among multiple options or solves complex decision problems.

### ScalingGroupResolver

ScalingGroupResolver validates whether the selected scaling group is usable from the filtered scaling group list.

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

The advantages of the pipeline pattern are: processing order is clear making the flow easy to understand, rules can be dynamically added or removed providing excellent extensibility, each stage operates independently with low coupling, and individual rules can be tested independently making testing easy.

## Error Handling

### ValidationError

ValidationError is the exception raised when a request is invalid during the validation stage. This exception includes which validation rule failed, the specific error message, the name and value of incorrect fields, and suggestions for resolving the problem when possible.

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

CalculationError is the exception raised when an error occurs during resource calculation. It includes the cause of calculation failure, input data used for calculation, and expected value range information.

### ResolutionError

ResolutionError is the exception raised when failing to find a suitable option. For example, it's raised when there's no scaling group satisfying the session's requirements. This exception includes the session's requirements, a list of reviewed options, and why each option is unsuitable.

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

When rule execution order is important, order can be explicitly specified:

```python
controller.set_validation_order([
    ClusterValidationRule,
    MountValidationRule,
    ScalingGroupFilteringRule
])
```

## Performance Considerations

### Validation Optimization

To optimize validation stage performance, use Fast Fail strategy to stop immediately at first validation failure, execute rules with no interdependencies in parallel, and cache and reuse repeated validation results for identical requests.

### Data Preparation Optimization

Data preparation process uses Lazy Evaluation to perform calculations only when actually needed, maximizes reuse of results generated in previous stages, and improves efficiency by batching multiple session creation requests for processing at once.

### Resource Calculation Optimization

Resource calculation caches and reuses calculation results for identical inputs, and achieves appropriate balance between accuracy and speed by using approximate calculation instead of exact calculation depending on situation.

## Monitoring and Debugging

### Metrics

To monitor system state, track validation success and failure counts, failure frequency per validation rule, time spent in preparation stage, time taken for resource calculation, and scaling group selection success rate.

## Troubleshooting

### 1. Repeated Validation Failures

**Symptoms**:
- Session creation requests continuously fail at validation stage

**Causes**:
- Incorrect request data
- System constraint violations

**Diagnosis**:
- **Check Error Message**: Review error message returned on session creation failure and failed rule
- **Request Data**: Validate cluster size, resource requests, mount paths, etc.
- **Constraints**: Check resource quotas, concurrent session count limits

**Resolution**:
1. Fix request data format and values
2. Check and adjust resource quotas
3. Review system constraints

### 2. Scaling Group Selection Failure

**Symptoms**:
- "No suitable scaling group found" error

**Causes**:
- No scaling group providing requested resources
- Insufficient scaling group permissions

**Diagnosis**:
- **Available Scaling Groups**: Check list of scaling groups accessible to user
- **Resource Requirements**: Verify which scaling groups can provide requested GPU, memory, etc.
- **Permission Settings**: Check scaling group access permissions per domain/group

**Resolution**:
1. Adjust resource requirements
2. Check and adjust user permissions
3. Validate scaling group configuration

### 3. Error in Preparation Stage

**Symptoms**:
- Session creation fails in preparation stage

**Causes**:
- Volume mount validation failure
- Cluster network configuration errors

**Diagnosis**:
- **Error Message**: Identify which preparation stage failed
- **Mount Configuration**: Check vfolder existence and permissions
- **External Services**: Check Storage, Network service status

**Resolution**:
1. Verify mount paths and vfolder permissions
2. Check external service status
3. Review cluster network configuration

### 4. Resource Calculation Error

**Symptoms**:
- Calculated resources differ from expected

**Causes**:
- Unit conversion errors
- Multiplier calculation errors according to cluster size

**Diagnosis**:
- **Requested Resources**: Check input resource values and units
- **Cluster Size**: Verify cluster mode and node count
- **Calculation Result**: Check final calculated total resources

**Resolution**:
1. Verify resource units (GB vs GiB, etc.)
2. Validate cluster size
3. Adjust resource request values if needed

## Parent Document
- [Sokovan Overall Architecture](../README.md)

## Related Documents
- [Scheduler Architecture](../scheduler/README.md)
- [Deployment Architecture](../deployment/README.md)
