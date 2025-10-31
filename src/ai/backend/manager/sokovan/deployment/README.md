# Deployment

← [Back to Sokovan](../README.md#sokovan-component-documentation) | [Manager](../../README.md#manager-architecture-documentation) | [Architecture Overview](../../../README.md#manager)

## Overview

Deployment is Backend.AI's deployment management system that handles deployment, scaling, and routing of various services including model serving (vLLM, TGI, SGLang, etc.).

**Key Responsibilities:**
- **Lifecycle Management**: Orchestrates the entire lifecycle from deployment creation to termination
- **Replica Management**: Handles creation, management, and auto-scaling of replicas
- **Type-specific Definition Generation**: Automatically generates session definitions tailored to each deployment type (vLLM, TGI, SGLang, etc.)
- **Routing Management**: Manages routes for deployed services and distributes traffic
- **Health Checks**: Detects unhealthy replicas through periodic monitoring and enables automatic recovery

## Architecture

```
┌─────────────────────────────────────────────┐
│      DeploymentCoordinator                  │
│  - Orchestrates deployment lifecycle        │
│  - Manages state-specific handlers          │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Deploy-   │ │ Route    │ │Handlers  │
│ment      │ │Control-  │ │          │
│Control-  │ │ler       │ │          │
│ler       │ │          │ │          │
└────┬─────┘ └────┬─────┘ └──────────┘
     │            │
     ▼            ▼
┌──────────┐ ┌──────────┐
│Defini-   │ │ Route    │
│tion      │ │Coordi-   │
│Gene-     │ │nator     │
│rators    │ │          │
└──────────┘ └──────────┘
```

## Dependencies

Deployment depends on the following infrastructure components:

**PostgreSQL**: Persists deployment, replica, and route states

**Redis (Valkey)**: Caches replica states, collects metrics

**etcd**: Shares global configuration

## Major Components

### DeploymentCoordinator

DeploymentCoordinator acts as the top-level orchestrator of deployment lifecycles and serves as the central hub of the deployment system. It periodically processes deployment lifecycles and invokes appropriate handlers based on each deployment's current state. It works closely with RouteController to automatically update routing configurations according to deployment state changes and propagates deployment-related events to other components.

**Key Methods:**
- `process_deployment_lifecycle()`: Processes the entire lifecycle of deployments
- `process_if_needed()`: Executes only when deployment processing is needed

**Processing Flow:**
```
1. Query active deployments
   ↓
2. Select handler by deployment state
   ↓
3. Execute handler
   ├─ PendingHandler: Initial setup
   ├─ ReplicaHandler: Replica management
   ├─ ScalingHandler: Auto-scaling
   └─ DestroyingHandler: Termination processing
   ↓
4. Update RouteController
```

### DeploymentController

DeploymentController performs the actual control logic for deployments. It handles basic CRUD operations such as creating, updating, and deleting deployments, and manages the replica count for each deployment. It automatically generates session definitions tailored to deployment types (vLLM, TGI, SGLang, etc.) and applies configured auto-scaling policies to deployments.

**Key Methods:**
- `create_deployment()`: Creates a new deployment
- `update_deployment()`: Updates deployment configuration
- `scale_deployment()`: Dynamically adjusts replica count
- `destroy_deployment()`: Deletes deployment
- `get_deployment_status()`: Queries current deployment state

**Deployment Creation Flow:**
```
1. Receive deployment request
   ↓
2. Select Definition Generator
   ↓
3. Create session creation request
   ↓
4. Request validation from SchedulingController
   ↓
5. Request session creation from Scheduler
   ↓
6. Save deployment record (PENDING)
   ↓
7. Request route creation from RouteController
```

## Definition Generators

Definition Generator is a strategy pattern that generates appropriate session creation requests based on deployment type. Since each deployment type (vLLM, TGI, SGLang, NIM, etc.) has different images, environment variables, and resource requirements, it is designed to abstract these differences and handle them through a consistent interface.

> **Note**: Specific configurations for each deployment type will be managed as DB-based fixtures in the future.

## State-Specific Handlers

The deployment system provides specialized handlers for each deployment state, performing necessary operations for each state.

### PendingHandler

PendingHandler handles the initial setup and preparation stage of deployments. This handler initializes deployments, generates session creation requests for the configured initial replica count, and prepares resources needed for the deployment.

**Processing Flow:**
```
1. Check deployment state (PENDING)
   ↓
2. Generate session definitions with Definition Generator
   ↓
3. Request session creation for replica count
   ↓
4. Deployment state → PROVISIONING
```

### ReplicaHandler

ReplicaHandler is responsible for managing replicas and synchronizing their states. This handler continuously monitors the state of each replica session, detects failed or abnormally terminated replicas and automatically regenerates them. To maintain the target replica count configured for the deployment, it creates new replicas when insufficient and removes them when excess.

**Processing Flow:**
```
1. Query current replica state
   ↓
2. Compare with target replica count
   ├─ Insufficient: Create new replicas
   ├─ Excess: Remove old replicas
   └─ Failed: Regenerate failed replicas
   ↓
3. Update deployment state
```

Replicas can have states such as HEALTHY (operating normally), UNHEALTHY (health check failed), STARTING (starting up), TERMINATING (shutting down), and the handler takes appropriate action based on this state information.

### ScalingHandler

ScalingHandler processes metric-based auto-scaling. This handler collects and analyzes metrics such as CPU utilization, memory utilization, request count, and response time, compares them with configured thresholds to make scale-up or scale-down decisions. Based on decisions, it dynamically adjusts replica count through DeploymentController.

**Scaling Policy:**
```python
{
    "min_replicas": 1,           # Minimum replica count
    "max_replicas": 10,          # Maximum replica count
    "target_metric": "cpu",      # Target metric
    "target_value": 70,          # Target value (%)
    "scale_up_threshold": 80,    # Scale-up threshold
    "scale_down_threshold": 30,  # Scale-down threshold
    "cooldown_period": 60        # Cooldown period
}
```

**Processing Flow:**
```
1. Query current metrics
   ↓
2. Compare with thresholds
   ├─ > scale_up_threshold
   │   └─ Increase replica count
   ├─ < scale_down_threshold
   │   └─ Decrease replica count
   └─ Normal range
       └─ Maintain
   ↓
3. Check cooldown period
   ↓
4. Execute scaling
```

### DestroyingHandler

DestroyingHandler is responsible for termination processing of deployments. This handler requests termination of all replicas belonging to the deployment, cleans up resources (network, storage, etc.) associated with the deployment, and removes routes for that deployment through RouteController.

**Processing Flow:**
```
1. Check deployment state (DESTROYING)
   ↓
2. Request termination of all replicas
   ↓
3. Confirm termination completion
   ↓
4. Request route removal from RouteController
   ↓
5. Delete deployment record or transition to TERMINATED state
```

## Route Management

The route management system handles network routing for deployed services. It distributes external client requests to appropriate replicas and dynamically adjusts routing based on replica state.

### RouteCoordinator

RouteCoordinator is the orchestrator of route lifecycles, selecting and executing appropriate handlers based on route state. It orchestrates health check tasks to detect unhealthy endpoints and updates the endpoint list in real-time as replicas are added or removed.

Key methods include `process_routes()` for processing routes, `handle_route_provisioning()` for handling the provisioning stage, `handle_route_running()` for managing running routes, and `handle_route_health_check()` for performing health checks.

### RouteController

RouteController performs the actual control logic for routes. It creates or updates new routes, configures traffic routing rules, and manages endpoint lists. It also applies load balancing strategies across multiple replicas.

Key methods include `create_route()` for creating new routes, `update_route()` for updating route configuration, `delete_route()` for deleting routes, and `get_endpoint()` for querying accessible endpoints.

**Route Creation Flow:**
```
1. Route creation request for deployment
   ↓
2. Create route record (PENDING)
   ↓
3. Collect replica endpoints
   ↓
4. Configure load balancer
   ↓
5. Create externally accessible endpoint
   ↓
6. Route state → RUNNING
```

### Route Handlers

#### ProvisioningHandler

ProvisioningHandler processes the provisioning stage of routes. It configures initial route setup, validates the validity of replica endpoints, and completes initial load balancer configuration.

#### RunningHandler

RunningHandler manages running routes. It routes client requests to appropriate replicas, synchronizes the endpoint list as replicas are added or removed, and applies configured load balancing policies. Load balancing strategies include ROUND_ROBIN which distributes sequentially, LEAST_CONNECTIONS which selects the endpoint with the fewest connections, and WEIGHTED which distributes based on weights.

#### HealthCheckHandler

HealthCheckHandler performs periodic health checks to verify normal operation of replicas. It detects unhealthy endpoints that don't respond or return errors, and triggers automatic recovery when configured thresholds are exceeded.

**Health Check Configuration:**
```python
{
    "interval": 10,            # Check interval
    "timeout": 5,              # Timeout
    "unhealthy_threshold": 3,  # Threshold for marking unhealthy
    "healthy_threshold": 2,    # Threshold for marking healthy
    "path": "/health",         # Health check path
    "method": "GET"            # HTTP method
}
```

**Processing Flow:**
```
1. Send health check requests to all endpoints
   ↓
2. Check responses
   ├─ Success: Increment healthy counter
   └─ Failure: Increment unhealthy counter
   ↓
3. Check thresholds
   ├─ Unhealthy threshold exceeded
   │   └─ Remove endpoint or restart replica
   └─ Healthy threshold reached
       └─ Activate endpoint
```

#### TerminatingHandler

TerminatingHandler is responsible for termination processing of routes. It blocks new requests and performs traffic draining by waiting for in-progress requests to complete, then removes endpoints and cleans up related resources once all requests are completed.

## Complete Processing Flow

### From Deployment Creation to Service

```
1. API: Receive deployment creation request
   ↓
2. DeploymentController.create_deployment()
   ├─ Validate deployment configuration
   ├─ Select Definition Generator
   └─ Generate session definitions
   ↓
3. Create deployment record (PENDING)
   ↓
4. DeploymentCoordinator.process_deployment_lifecycle()
   └─ Execute PendingHandler
       ├─ Request session creation for replica count
       └─ State → PROVISIONING
   ↓
5. Scheduler: Schedule and start sessions
   ↓
6. ReplicaHandler (periodic)
   ├─ Monitor replica state
   └─ Maintain target replica count
   ↓
7. RouteController.create_route()
   ├─ Create route
   ├─ Collect endpoints
   └─ Configure load balancer
   ↓
8. RouteCoordinator.process_routes()
   └─ Execute HealthCheckHandler
       ├─ Perform health checks
       └─ Handle unhealthy replicas
   ↓
9. Deployment state → RUNNING
   ↓
10. Provide externally accessible endpoint
```

### Auto-Scaling Flow

```
1. ScalingHandler (periodic)
   ↓
2. Query current metrics
   ├─ CPU utilization
   ├─ Memory utilization
   ├─ Request count
   └─ Response time
   ↓
3. Make scaling decision
   ├─ Scale-up needed
   │   └─ DeploymentController.scale_deployment(+1)
   ├─ Scale-down needed
   │   └─ DeploymentController.scale_deployment(-1)
   └─ Maintain
   ↓
4. Adjust replica count
   ├─ Add: Request new session creation
   └─ Remove: Terminate old sessions
   ↓
5. RouteController.update_route()
   └─ Update endpoint list
   ↓
6. Wait for cooldown period
```

## State Transition Details

### Deployment State Transitions

Deployments follow these state transition paths:

```
PENDING → PROVISIONING → RUNNING → DESTROYING → TERMINATED
```

**Transition Condition Details:**

| Current State | Next State | Transition Trigger | Responsible Component | Failure Handling |
|----------|----------|------------|--------------|------------|
| PENDING | PROVISIONING | Initial replica creation started | PendingHandler | ERROR (Generator failure) |
| PROVISIONING | RUNNING | Minimum replica count achieved | ReplicaHandler | PENDING (retry) |
| RUNNING | DESTROYING | Delete request received | DeploymentController | - |
| DESTROYING | TERMINATED | All replicas terminated | DestroyingHandler | - |

**Key Rules:**
- PROVISIONING state requires at least one HEALTHY replica
- Replica count can change dynamically even in RUNNING state
- New replica creation is not allowed after DESTROYING starts

### Replica State Transitions

Replicas follow these state transition paths:

```
         ┌─→ HEALTHY ←─┐
STARTING ┤      ↕       ├─→ TERMINATING → TERMINATED
         └─→ UNHEALTHY ┘
```

> **Note**: HEALTHY and UNHEALTHY states can transition bidirectionally based on health check results.

**Transition Condition Details:**

| Current State | Next State | Transition Trigger | Responsible Component | Retry Policy |
|----------|----------|------------|--------------|------------|
| STARTING | HEALTHY | Consecutive health check successes | HealthCheckHandler | - |
| STARTING | UNHEALTHY | Startup timeout or health check failure | HealthCheckHandler | Regenerate |
| HEALTHY | UNHEALTHY | Consecutive health check failures | HealthCheckHandler | Attempt restart |
| UNHEALTHY | HEALTHY | Consecutive health check successes | HealthCheckHandler | - |
| HEALTHY | TERMINATING | Termination request or scale-down | ReplicaHandler | - |
| UNHEALTHY | TERMINATING | Recovery failure or termination request | ReplicaHandler | - |
| TERMINATING | TERMINATED | Session termination completed | Scheduler | Force terminate |

**Retry Policies:**
- **Health check failure**: Transition to UNHEALTHY when configured unhealthy_threshold reached
- **UNHEALTHY recovery**: Attempt restart, terminate and regenerate if failed
- **Termination failure**: Force terminate after timeout

### Route State Transitions

Routes follow these state transition paths:

```
PENDING → PROVISIONING → RUNNING → TERMINATING → TERMINATED
```

**Transition Condition Details:**

| Current State | Next State | Transition Trigger | Responsible Component |
|----------|----------|------------|--------------|
| PENDING | PROVISIONING | Route creation started | RouteController |
| PROVISIONING | RUNNING | Endpoint collection completed, load balancer configured | ProvisioningHandler |
| RUNNING | TERMINATING | Deployment termination or route deletion | RouteController |
| TERMINATING | TERMINATED | Traffic draining completed | TerminatingHandler |

## Configuration and Tuning

### Deployment Type-Specific Configuration

Each deployment type (vLLM, TGI, SGLang, etc.) requires different configuration. Refer to each Definition Generator's documentation to identify and apply appropriate configuration for the deployment type.

### Replica Configuration

Replica-related configurations include `min_replicas` specifying the minimum replica count to maintain, `max_replicas` limiting the maximum replica count that auto-scaling can increase to, and `initial_replicas` setting the initial replica count to start when creating the deployment.

### Scaling Policy

Auto-scaling policy is configured by selecting the metric type to monitor (cpu, memory, requests, latency, etc.), setting thresholds to trigger scale-up and scale-down, and specifying the cooldown period which is the minimum wait time between consecutive scaling operations.

### Health Check Configuration

Health checks are configured by setting check interval and timeout, specifying thresholds for marking replicas as unhealthy or healthy, and setting the HTTP path and method for performing health checks.

### Routing Configuration

Routing-related configurations include selecting the load balancing strategy to use (round-robin, least connections, weight-based), setting request timeout, and configuring retry policy for failed requests.

## Performance Considerations

### Replica Management

As the number of replicas increases, monitoring load also increases, so appropriate monitoring intervals should be set according to system scale. Using batch processing instead of handling multiple replicas individually can improve efficiency.

### Health Checks

Health check intervals should be set considering the tradeoff between accuracy and load. Checking too frequently causes unnecessary network load, while checking too infrequently can delay failure detection.

### Scaling

Minimize decision latency to enable fast response, but set cooldown periods appropriately to prevent unnecessary scaling fluctuations. Also consider the cost of metric collection and selectively collect only necessary metrics.

### Routing

Appropriately adjust the update frequency of endpoint lists, minimize overhead from load balancing, and improve performance by caching frequently queried information.

## Extension Points

### Adding New Definition Generator

To support a new deployment type, inherit from `BaseDefinitionGenerator`, implement the `generate()` method for generating session definitions and the `validate()` method for validating configuration, then register in DefinitionGeneratorRegistry.

### Adding New Scaling Metric

To support new metric-based scaling, implement metric collection logic, add the metric to scaling policy, and update ScalingHandler to process the new metric.

### Adding New Load Balancing Strategy

To add a new load balancing algorithm, implement the strategy class and integrate it into RouteController to provide as a selectable option.

## Monitoring and Debugging

### Metrics

To monitor system state, track deployment creation, update, and deletion counts, changes in replica count over time, frequency of scaling events, success and failure rates of health checks, and average response time of endpoints.

## Troubleshooting

### 1. Deployment Stuck in PENDING/PROVISIONING State

**Symptoms**:
- Deployment remains in PENDING or PROVISIONING state for extended time
- No replica creation

**Causes**:
- Deployment configuration errors such as model definition
- Session creation failure due to insufficient resources
- Scaling group configuration errors

**Diagnosis**:
- **Deployment Details**: Check deployment configuration and scaling policy
- **Replica Sessions**: Verify if replica sessions were actually created, check session state
- **Session History**: Identify session creation failure reasons
- **Scaling Group Resources**: Check available resources

**Resolution**:
1. Validate deployment configuration (model name, resource requests, etc.)
2. Check scaling group resource availability
3. Identify session creation failure cause from Session History

### 2. Auto-Scaling Not Working

**Symptoms**:
- No replica count increase despite high load
- No replica count decrease despite low load

**Causes**:
- Metric collection failure
- Scaling policy configuration errors
- Waiting within cooldown period
- New session creation impossible due to insufficient resources

**Diagnosis**:
- **Scaling Policy**: Check min/max replica count and thresholds
- **Current Metrics**: Check current metric values like CPU, memory, RPS
- **Replica State**: Check current replica count and state distribution
- **Session Creation Possibility**: Check scaling group available resources and session creation success

**Resolution**:
1. Check metric collection status
2. Validate scaling policy configuration
3. Adjust cooldown period
4. Add agents or secure resources if resource shortage

> **Note**: Scale-up can fail if unable to create new sessions due to resource shortage even if metrics are normal.

## Parent Document
- [Sokovan Overall Architecture](../README.md)

## Related Documents
- [Scheduler Architecture](../scheduler/README.md)
- [SchedulingController Architecture](../scheduling_controller/README.md)
