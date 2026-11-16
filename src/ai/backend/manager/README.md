# Backend.AI Manager

← [Back to Architecture Overview](../README.md#manager)

## Purpose

The manager is the central orchestrator of the Backend.AI cluster. It schedules sessions and kernels, allocates resources, manages the session lifecycle, and provides the API gateway through REST and GraphQL.

## Key Responsibilities

### 1. API Gateway
- Serve the REST API and the GraphQL API to clients
- Authenticate and authorize requests
- Apply rate limits and manage quotas
- Manage API versions

### 2. Session Scheduling
- Allocate computing resources for session requests
- Select the best agents through various scheduling algorithms
- Manage the session lifecycle (creation, execution, termination)
- Schedule and manage cluster-mode sessions

### 3. Resource Management
- Track cluster-wide resource status
- Collect and aggregate agent resource information
- Manage resource allocation and release
- Handle resource presets and quotas

### 4. User and Organization Management
- Manage user accounts and authentication
- Manage projects, domains, and their organization
- Manage permissions and role-based access control
- Manage credentials (access key and secret key)

### 5. vfolder management
- Provide persistent storage to users
- Integrate various storage backends
- Manage file upload and download
- Manage vfolder sharing and permissions

### 6. Image Registry Management
- Manage container registries
- Scan and synchronize image metadata
- Validate and manage image versions
- Control allowed images per domain

## Entry Points

The manager accepts and processes external requests through four entry points.

### 1. REST API

**Framework**: aiohttp (asynchronous HTTP web framework)

**Location**: `src/ai/backend/manager/api/`

**Key Features**:
- HTTP/HTTPS-based communication
- JSON request/response format
- JWT or API key authentication
- Validation and authentication through the middleware stack

**Processing Flow**:
```
HTTP Request → Middleware Stack → REST Handler → Action Processor → Service → Repository → DB
```

**Related documents**: [REST API documentation](./api/README.md)

### 2. GraphQL API

**Framework**: Strawberry (current) and Graphene (legacy, deprecated)

**Location**:
- Strawberry: `src/ai/backend/manager/api/gql/`
- Graphene (legacy): `src/ai/backend/manager/api/gql_legacy/`

**Related documents**:
- [GraphQL API (Strawberry)](./api/gql/README.md)
- [Legacy GraphQL (Graphene)](./api/gql_legacy/README.md) - deprecated

### 3. Event Dispatcher

**Framework**: Backend.AI Event Dispatcher

**Location**: `src/ai/backend/common/events/`

**Event Types**:
- **Broadcast Events**: Received by every manager instance
- **Anycast Events**: Received by only one manager instance

**Processing Flow**:
```
Event Producer → Event Dispatcher → Event Handler → Service
```

**Related documents**: [Event Dispatcher System](../common/events/README.md)

### 4. Background Task Handler

**Framework**: Backend.AI Background Task Handler

**Location**: `src/ai/backend/common/bgtask/`

**Purpose**:
Handles long-running tasks asynchronously. It issues a task ID that lets a client subscribe to progress updates or results through events.

**Processing Flow**:
```
Task Request → Background Task Handler → Task Execute → Event Notification
```

**Related documents**: [Background Task Handler System](../common/bgtask/README.md)

### Entry Point Interactions

Each entry point runs independently, but service logic can start a background task or publish an event when needed.

**Interaction Examples**:
```
REST API Handler → Service Logic → Event Publish (notify other Manager instances)
Event Handler → Service Logic → Background Task Trigger (when async processing needed)
```

**Integrated Architecture**:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  REST API   │  │ GraphQL API │  │   Event     │  │ Background  │
│  (aiohttp)  │  │(Strawberry) │  │ Dispatcher  │  │    Task     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Services Layer    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Repositories Layer │
                    └────────────────────┘
```

## Architecture

```
┌───────────────────────────────────────────┐
│              API Layer                    │
│  - REST API Handler (aiohttp)             │
│  - GraphQL Handler (strawberry)           │
│  - Authentication & Authorization         │
│  - Request Validation                     │
└──────────────────┬────────────────────────┘
                   │
┌──────────────────┴────────────────────────┐
│            Actions Layer                  │
│  - Session Lifecycle Actions              │
│  - Resource Allocation Actions            │
│  - User Management Actions                │
│  - VFolder Management Actions             │
└──────────────────┬────────────────────────┘
                   │
┌──────────────────┴────────────────────────┐
│           Services Layer                  │
│  - Scheduling Service                     │
│  - Session Management Service             │
│  - Resource Quota Service                 │
│  - Event Processing Service               │
└──────────────────┬────────────────────────┘
                   │
┌──────────────────┴────────────────────────┐
│         Repositories Layer                │
│  - Session Repository                     │
│  - Agent Repository                       │
│  - User Repository                        │
│  - VFolder Repository                     │
└──────────────────┬────────────────────────┘
                   │
┌──────────────────┴────────────────────────┐
│            Models Layer                   │
│  - SQLAlchemy ORM Models                  │
│  - Domain Types                           │
└───────────────────────────────────────────┘
```

## Directory Structure

```
manager/
├── models/              # Database schema and ORM models
│   ├── alembic/        # Database migration scripts
│   ├── user.py         # User and credential models
│   ├── session.py      # Session and kernel models
│   ├── agent.py        # Agent models
│   ├── vfolder.py      # Virtual folder models
│   ├── scaling_group.py # Scaling group models
│   └── ...
├── repositories/        # Data access layer
│   ├── session/        # Session data access
│   ├── agent/          # Agent data access
│   ├── user/           # User data access
│   └── ...
├── services/            # Business logic layer
│   ├── session/        # Session lifecycle management
│   └── ...
├── api/                 # API handlers and routes
│   ├── gql/             # GraphQL schema and resolvers
│   ├── auth.py          # Authentication handlers
│   └── ...
├── config/              # Configuration management
├── cli/                 # CLI commands
│   ├── fixture.py       # Test data management
│   └── ...
├── clients/             # External service clients
│   ├── agent/           # Agent RPC client
│   ├── storage_proxy/   # Storage proxy client
│   └── ...
├── scheduler/           # Scheduling algorithms and logic
│   ├── dispatcher.py   # Scheduling dispatcher
│   ├── predicates.py   # Scheduling predicates
│   └── ...
├── server.py            # Main server entry point
└── defs.py              # Shared constants and types
```

## Core Concepts

### Sessions
A session is a user compute request and has one or more kernels:
- **Session ID**: Unique identifier for the session
- **Access Key**: The owner's API access key
- **Status**: Session status (PENDING, RUNNING, TERMINATED, and others)
- **Resource Allocation**: Allocated CPU, memory, and GPU resources
- **Cluster Size**: Number of kernels in multi-container mode

Session Lifecycle:
1. A user creates a session through the API.
2. The manager schedules it and allocates resources.
3. The Agent creates and starts the kernel containers.
4. The user executes code and uses services.
5. The session terminates (user request or timeout).
6. Resources return to the pool.

### Agents
Agents run kernels on nodes:
- **Agent ID**: Unique identifier for the agent
- **Status**: Agent status (ALIVE, LOST, TERMINATED)
- **Available Resources**: CPU, memory, and GPU capacity
- **Occupied Slots**: Resources allocated at the moment
- **Resource Group**: The resource group to which the agent belongs

Agent monitoring:
- The manager checks agent health periodically.
- The Agent sends agent heartbeats and resource status updates.
- Lost agents are detected automatically.
- Kernels are rebalanced during a failure.

### Resource Groups
A resource group manages a set of agents logically:
- **Name**: Unique identifier for the resource group
- **Scheduler Type**: Scheduling algorithm (FIFO, LIFO, DRF, and others)
- **Agent Members**: Agents in the resource group
- **Allowed vfolder hosts**: Permitted storage backends
- **Resource Limits**: Resource limits per resource group

### vfolders
A vfolder provides persistent storage:
- **Folder Name**: User-defined folder name
- **Host**: Storage backend location
- **Ownership**: User or project ownership
- **Permissions**: Read and write permissions
- **Quota**: Storage capacity limit

## Infrastructure Dependencies

### Required Infrastructure

#### PostgreSQL (Persistent Data)
- **Purpose**:
  - Store all Backend.AI metadata
  - User, project, and domain information
  - Session and kernel history
  - vfolder metadata
  - Resource allocation records
- **Halfstack Port**: 8101 (host) → 5432 (container)
- **Key Tables**:
  - `users`, `keypairs` - User credentials
  - `groups`, `domains` - Organization structure
  - `kernels`, `sessions` - Session information
  - `agents` - Agent status
  - `vfolders` - vfolder metadata
  - `scaling_groups` - Resource group configuration

#### Valkey (Caching and Real-time Data)
- **Purpose**:
  - Cache frequently accessed data
  - Distributed locking
  - Agent live status tracking
  - Session rate limiting
  - Temporary session data storage
- **Halfstack Port**: 8111 (host) → 6379 (container)

#### etcd (Global Configuration)
- **Purpose**:
  - Store cluster-wide configuration
  - Service discovery
  - Agent registration
  - Dynamic configuration updates
- **Halfstack Port**: 8121 (host) → 2379 (container)

### Optional Infrastructure (Observability)

#### Prometheus (Metrics Collection)
- **Purpose**:
  - API request metrics
  - Session scheduling metrics
  - Resource usage metrics
  - Background task metrics
- **Internal Port**: 18080 (separate from main API port 8091)
- **Exposed Endpoints**:
  - `http://localhost:18080/metrics` - Prometheus metrics endpoint
  - `http://localhost:18080/metrics/service_discovery` - Service discovery endpoint that automates the metrics collection configuration
- **Key Metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time
  - `backendai_scheduler_enqueue_success` - Successful scheduling count
  - `backendai_agent_registry_count` - Number of agents
- **Note**: The service discovery endpoint gives Prometheus the configuration to discover every Backend.AI component endpoint automatically

#### Loki (Log Aggregation)
- **Purpose**:
  - Session lifecycle events
  - API request/response logs
  - Scheduling decision logs
  - Error and exception logs
- **Log Labels**:
  - `component` - Component identifier (manager)
  - `session_id` - Session identifier
  - `user_id` - User identifier
  - `level` - Log level (info, warning, error)

#### Grafana (Visualization)
- **Purpose**:
  - Real-time metrics dashboards
  - Resource usage visualization
  - Session status monitoring
  - Alert management

## Configuration

See `configs/manager/halfstack.conf` for configuration file examples.

### Key Configuration Items

**Database Settings**:
- PostgreSQL connection string
- Connection pool size
- Query timeout settings

**Valkey Settings**:
- Valkey connection information
- Connection pool configuration

**etcd Settings**:
- etcd endpoint addresses
- Configuration key prefix (namespace)

**API Settings**:
- Listen address and port
- CORS configuration

**Scheduling Settings**:
- Default scheduler type
- Scheduling interval
- Resource allocation policy

### Halfstack Configuration

**Recommended**: use the `./scripts/install-dev.sh` script to set up the development environment.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Manager
./backend.ai mgr start-server
```

#### API Access
- REST API: http://localhost:8081
- GraphQL API: http://localhost:8081/graphql
- Admin GraphQL UI: http://localhost:8081/graphql-ui

## Metrics and Monitoring

### Prometheus Metrics

The manager exposes Prometheus metrics at the `/metrics` endpoint to monitor system health and performance.

#### Label Conventions

Many metrics share labels for error tracking and classification:

**Error-related Labels** (populated only when an error occurs):
- `domain`: Error domain that classifies the error source (for example, "session", "agent", "storage")
- `operation`: Operation that failed (for example, "create", "terminate", "allocate")
- `error_detail`: Detailed error information for debugging

**Status Labels**:
- `status`: Result of the operation, usually "success" or "failure"
- `success`: Boolean string ("True" or "False") that tells whether the operation succeeded

#### API Metrics

REST API request monitoring metrics.

**`backendai_api_request_count`** (Counter)
- **Description**: Total number of REST API requests received
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: API endpoint path (for example, "/v1/session/create")
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
  - `status_code`: HTTP response status code (200, 400, 500, and others)

**`backendai_api_request_duration_sec`** (Histogram)
- **Description**: API request processing time in seconds
- **Labels**: Same as `backendai_api_request_count`

#### GraphQL Metrics

GraphQL query execution monitoring metrics.

**`backendai_graphql_request_count`** (Counter)
- **Description**: Total number of GraphQL queries executed
- **Labels**:
  - `operation_type`: GraphQL operation type (query, mutation, subscription)
  - `field_name`: GraphQL field being accessed
  - `parent_type`: Parent type in the GraphQL schema
  - `operation_name`: Named operation from the query
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
  - `success`: "True" or "False" indicating query success

**`backendai_graphql_request_duration_sec`** (Histogram)
- **Description**: GraphQL query processing time in seconds
- **Labels**: Same as `backendai_graphql_request_count`

#### Event Metrics

Internal event processing metrics.

**`backendai_event_count`** (Counter)
- **Description**: Total number of events processed
- **Labels**:
  - `event_type`: Type of event (for example, "session_terminated", "kernel_started")

**`backendai_event_failure_count`** (Counter)
- **Description**: Number of failed event processing attempts
- **Labels**:
  - `event_type`: Type of event that failed
  - `exception`: Exception class name (for example, "SessionNotFound", "AgentError")
  - `domain`: Error domain
  - `operation`: Error operation
  - `error_detail`: Error details

**`backendai_event_processing_time_sec`** (Histogram)
- **Description**: Event processing time in seconds
- **Labels**:
  - `event_type`: Type of event
  - `status`: "success" or "failure"
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)

#### Background Task Metrics

Periodic and scheduled task execution metrics.

**`backendai_bgtask_count`** (Gauge)
- **Description**: Number of currently running background tasks
- **Labels**:
  - `task_name`: Background task identifier (for example, "recalc_agent_resource_occupancy")

**`backendai_bgtask_done_count`** (Counter)
- **Description**: Total number of completed background tasks
- **Labels**:
  - `task_name`: Background task identifier
  - `status`: "success" or "failure"
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)

**`backendai_bgtask_processing_time_sec`** (Histogram)
- **Description**: Background task execution time in seconds
- **Labels**: Same as `backendai_bgtask_done_count`

#### Action Metrics

High-level business operation metrics.

**`backendai_action_count`** (Counter)
- **Description**: Total number of actions executed
- **Labels**:
  - `entity_type`: Type of entity being operated on (for example, "session", "kernel", "agent")
  - `operation_type`: Type of operation (for example, "create", "terminate", "restart")
  - `status`: "success" or "failure"
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
- **Example**: Tracks session creation, termination, and other major lifecycle operations

**`backendai_action_duration_sec`** (Histogram)
- **Description**: Action execution time in seconds
- **Labels**: Same as `backendai_action_count`

#### Layer Operation Metrics

Granular metrics for operations at each architectural layer.

**`backendai_layer_operation_triggered_count`** (Gauge)
- **Description**: Number of layer operations currently in progress
- **Labels**:
  - `domain`: Domain type (valkey, repository, client)
  - `layer`: Specific layer (for example, "session_repository", "agent_client", "valkey_live")
  - `operation`: Operation name (for example, "fetch_session", "create_kernel")

**`backendai_layer_operation_count`** (Counter)
- **Description**: Total number of layer operations completed
- **Labels**:
  - `domain`: Domain type (valkey, repository, client)
  - `layer`: Specific layer identifier
  - `operation`: Operation name
  - `success`: "True" or "False"

**`backendai_layer_operation_error_count`** (Counter)
- **Description**: Total number of layer operation errors
- **Labels**:
  - `domain`: Domain type
  - `layer`: Specific layer identifier
  - `operation`: Operation name
  - `error_code`: Error code or "internal_error"

**`backendai_layer_retry_count`** (Counter)
- **Description**: Number of retries for layer operations
- **Labels**:
  - `domain`: Domain type
  - `layer`: Specific layer identifier
  - `operation`: Operation name

**`backendai_layer_operation_duration_sec`** (Histogram)
- **Description**: Layer operation execution time in seconds
- **Labels**:
  - `domain`: Domain type
  - `layer`: Specific layer identifier
  - `operation`: Operation name
  - `success`: "True" or "False"

#### System Metrics

System resource usage metrics.

**`backendai_async_task_count`** (Gauge)
- **Description**: Number of active asyncio tasks
- **Labels**: None

**`backendai_cpu_usage_percent`** (Gauge)
- **Description**: CPU usage percentage of the manager process
- **Labels**: None

**`backendai_memory_used_rss`** (Gauge)
- **Description**: Resident Set Size (RSS) memory usage in bytes
- **Labels**: None

**`backendai_memory_used_vms`** (Gauge)
- **Description**: Virtual Memory Size (VMS) in bytes
- **Labels**: None

#### Sweeper Metrics

Resource cleanup and garbage collection metrics.

**`backendai_sweep_session_count`** (Counter)
- **Description**: Total number of session cleanup operations
- **Labels**:
  - `status`: Session status being cleaned (for example, "TERMINATED", "ERROR")
  - `success`: "True" or "False"

**`backendai_sweep_kernel_count`** (Counter)
- **Description**: Total number of kernel cleanup operations
- **Labels**:
  - `success`: "True" or "False"

#### Event Propagator Metrics

External event propagation metrics for webhooks and integrations.

**`backendai_event_propagator_count`** (Gauge)
- **Description**: Current number of active event propagators
- **Labels**: None

**`backendai_event_propagator_alias_count`** (Gauge)
- **Description**: Current number of event propagator aliases
- **Labels**:
  - `domain`: Domain identifier for the alias
  - `alias_id`: Unique identifier for the propagator alias

**`backendai_event_propagator_registration_count`** (Counter)
- **Description**: Total number of event propagator registrations
- **Labels**: None

**`backendai_event_propagator_unregistration_count`** (Counter)
- **Description**: Total number of event propagator unregistrations
- **Labels**: None

#### Stage Metrics

Development and debugging metrics for tracking execution stages.

**`backendai_stage_count`** (Counter)
- **Description**: Count of stage occurrences for debugging and tracing
- **Labels**:
  - `stage`: Stage identifier
  - `upper_layer`: Calling layer or component

### Prometheus Query Examples

The examples below show common Prometheus queries for manager metrics. Counter metrics take the `_total` suffix, and Histogram metrics take the `_bucket`, `_sum` and `_count` suffixes in an actual query.

**Important Notes:**
- A query with `increase()` or `rate()` needs a time range at least 2-4 times the Prometheus scrape interval for reliable data. A shorter range may show metrics as absent or incomplete.
- The default Prometheus scrape interval is usually 15s-30s.
- **Time range selection trade-offs**:
  - Shorter ranges (for example, `[1m]`): detect a change faster with finer data, but are more sensitive to noise and short-term fluctuation
  - Longer ranges (for example, `[5m]`): smoother graphs with less noise, better for identifying a trend, but slower to detect a sudden change
  - For real-time alerting: use a shorter range such as `[1m]` or `[2m]`
  - For dashboards and trend analysis: use a longer range such as `[5m]` or `[10m]`

#### API Request Rate

**API Request Rate by Endpoint**

Calculate the per-second rate of API requests grouped by API endpoint and status. It shows how many requests per second each API endpoint receives. Use it to find high-traffic endpoints and monitor the overall API load.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[1m])) by (method, endpoint, status_code)
```

**Failed API Requests (5xx Errors)**

Monitor failed API requests (5xx errors) to find service issues and detect internal errors in the manager.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"5.."}[5m])) by (endpoint)
```

#### API Request Duration

**P95 API Request Latency**

Calculate the 95th percentile (P95) latency of API requests. It shows the response time within which 95% of requests complete. Use it to find slow endpoints and set SLA targets.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups"}[5m])) by (le, endpoint)
)
```

**Average API Request Duration**

Calculate the average request duration per endpoint. It gives a simple view of typical response times.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups"}[5m])) by (endpoint)
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups"}[5m])) by (endpoint)
```

#### GraphQL Query Performance

**GraphQL Query Rate by Operation**

Monitor the GraphQL query rate by operation type and field. Use it to see which GraphQL queries run most often.

```promql
sum(rate(backendai_graphql_request_count_total{service_group="$service_groups"}[5m])) by (operation_type, field_name)
```

**Failed GraphQL Queries**

Track failed GraphQL queries with error details. It finds problematic queries and common error patterns.

```promql
sum(rate(backendai_graphql_request_count_total{service_group="$service_groups", success="False"}[5m])) by (field_name, error_detail)
```

#### Layer Operation Performance

**P95 Valkey Operation Latency**

Monitor Valkey operation latency (P95) by layer and operation. It finds slow Valkey operations that may cause a bottleneck. Broadcast and stream operations are excluded because their performance characteristics differ.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="valkey", operation!~"receive_broadcast_message|read_consumer_group"}[5m])) by (le, layer, operation)
)
```

**P95 Database Repository Latency**

Monitor database repository operation latency (P95). Use it to find slow database queries and optimize data access.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="repository"}[5m])) by (le, layer, operation)
)
```

**P95 Agent RPC Call Latency**

Monitor Agent RPC call latency (P95). It shows how long communication with an agent takes.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="client", layer="agent_client"}[5m])) by (le, operation)
)
```

**Failed Layer Operations**

Track failed layer operations to find integration issues. A high error rate points to an external dependency problem or an internal defect.

```promql
sum(rate(backendai_layer_operation_count_total{success="False"}[5m])) by (domain, layer, operation)
```

#### Background Tasks

**Currently Running Background Tasks**

Monitor background tasks that are running. The Gauge metric shows the live count of active tasks. Use it to confirm that background tasks run and to detect a stuck task.

```promql
sum(backendai_bgtask_count) by (task_name)
```

**Background Task Completion Rate**

Track the background task completion rate and the success or failure status. It shows how often tasks complete and their success rate.

```promql
sum(rate(backendai_bgtask_done_count_total[5m])) by (task_name, status)
```

**Failed Background Tasks**

Monitor failed background tasks with error details. Use it to find recurring task failures and debug them.

```promql
sum(rate(backendai_bgtask_done_count_total{status="failure"}[5m])) by (task_name, error_detail)
```

#### Event Processing

**Event Processing Rate by Type**

Monitor the event processing rate by event type. It shows how many events are processed per second. Use it to see event throughput and detect a processing delay.

```promql
sum(rate(backendai_event_count_total[5m])) by (event_type)
```

**Event Processing Failures**

Track event processing failures by exception type. It finds problematic event handlers and common error patterns.

```promql
sum(rate(backendai_event_failure_count[5m])) by (event_type, exception)
```

**P95 Event Processing Duration**

Calculate P95 event processing duration. It shows the processing time per event type. Use it to find slow event handlers that may cause a delay.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_event_processing_time_sec_bucket[5m])) by (le, event_type)
)
```

#### Action Metrics

**Action Execution Rate**

Monitor the action execution rate grouped by entity and operation type. It shows the rate of operations such as session creation. Use it to see system activity and user behavior.

```promql
sum(rate(backendai_action_count_total[5m])) by (entity_type, operation_type, status)
```

**Failed Actions**

Track failed actions with detailed error information. It shows which operations fail and why.

```promql
sum(rate(backendai_action_count_total{status="failure"}[5m])) by (entity_type, operation_type, error_detail)
```

**P95 Action Execution Duration**

Calculate P95 action execution duration. It shows how long key operations take. Use it to set performance expectations and find slow operations.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_action_duration_sec_bucket[5m])) by (le, entity_type, operation_type)
)
```

#### System Resources

Monitor active asyncio tasks in the event loop. A high task count may point to a resource leak or excessive concurrency.

```promql
backendai_async_task_count
```

Monitor the CPU usage percentage of the manager process. Use it to detect a CPU bottleneck and plan capacity.

```promql
backendai_cpu_usage_percent
```

Monitor the Resident Set Size (physical memory usage). It shows the actual RAM usage of the manager process.

```promql
backendai_memory_used_rss
```

Monitor the Virtual Memory Size (total allocated memory). It includes swapped memory and memory-mapped files.

```promql
backendai_memory_used_vms
```

#### Session Sweeper

Monitor session cleanup operations by session status. It shows how many sessions are cleaned up and the success rate. Use it to confirm that resources are cleaned up and to find a cleanup issue.

```promql
sum(rate(backendai_sweep_session_count_total[5m])) by (status, success)
```

Monitor the kernel cleanup operation rate. It tracks cleanup of orphaned kernels.

```promql
sum(rate(backendai_sweep_kernel_count_total[5m])) by (success)
```

### Logs
- API request and response logs
- Session scheduling decision logs
- Resource allocation and release events
- Authentication and authorization events
- Background task execution logs
- Error and exception stack traces

## Communication Protocols

### Agent Communication
- **Protocol**: ZeroMQ RPC
- **Port**: 6011 (agent RPC server)
- **Main Operations**: Kernel lifecycle management, code execution, file operations, container statistics

### Storage Proxy Communication
- **Protocol**: HTTP
- **Port**: 6021 (storage proxy client API), 6022 (storage proxy manager API)
- **Main Operations**: vfolder management, file upload and download, file listing

### etcd Communication
- **Protocol**: gRPC (etcd v3 API)
- **Port**: 2379
- **Main Operations**: Configuration management, service discovery, watch notifications

## Development

See [README.md](./README.md) for development setup instructions.

## Manager Architecture Documentation

### Internal Architecture
- **[Sokovan Orchestration System](./sokovan/README.md)**: Session scheduling orchestrator with a three-tier architecture
  - [Scheduler](./sokovan/scheduler/README.md): Core scheduling engine for session placement and resource allocation
  - [Scheduling Controller](./sokovan/scheduling_controller/README.md): Validation and preparation for scheduling
  - [Deployment Controller](./sokovan/deployment/README.md): Deployment lifecycle management
- **[Services Layer](./services/README.md)**: Business logic patterns, design principles, and implementation guidelines
- **[Repositories Layer](./repositories/README.md)**: Data access patterns, query optimization, and transaction management
- **[Actions Layer](./actions/README.md)**: Permission validation, monitoring, and request handling

### Related documents
- [Agent Component](../agent/README.md): Kernel lifecycle management on nodes
- [Storage Proxy Component](../storage/README.md): vfolder and storage backend management
- [Webserver Component](../web/README.md): Web UI hosting and session management
- [Overall Architecture](../README.md): System-wide architecture and component interactions
