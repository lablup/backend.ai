# Backend.AI Manager

← [Back to Architecture Overview](../README.md#manager)

## Purpose

The Manager is the central orchestrator of the Backend.AI cluster. It schedules computing sessions (sessions and kernels), allocates resources, manages the lifecycle of sessions, and provides API gateway functionality through REST and GraphQL interfaces.

## Key Responsibilities

### 1. API Gateway
- Provide REST API and GraphQL API to clients
- Request authentication and authorization
- Rate limiting and quota management
- API versioning management

### 2. Session Scheduling
- Allocate computing resources for user compute session requests
- Select optimal agents based on various scheduling algorithms
- Manage session lifecycle (creation, execution, termination)
- Cluster-mode session scheduling and management

### 3. Resource Management
- Track cluster-wide resource status
- Collect and aggregate agent resource information
- Manage resource allocation and release
- Handle resource presets and quotas

### 4. User and Organization Management
- User account and authentication management
- Group and domain organization management
- Permission and role-based access control
- Credential (access key/secret key) management

### 5. Virtual Folder Management
- Provide persistent storage to users
- Integrate various storage backends
- Manage file upload/download
- Manage folder sharing and permissions

### 6. Image Registry Management
- Manage container image repositories
- Scan and synchronize image metadata
- Validate and manage image versions
- Control allowed images per domain

## Entry Points

The Manager accepts and processes external requests through 4 entry points.

### 1. REST API

**Framework**: aiohttp (async HTTP web framework)

**Location**: `src/ai/backend/manager/api/`

**Key Features**:
- HTTP/HTTPS-based communication
- JSON request/response format
- JWT or API Key-based authentication
- Validation and authentication via middleware stack

**Processing Flow**:
```
HTTP Request → Middleware Stack → REST Handler → Action Processor → Service → Repository → DB
```

**Related Documentation**: [REST API Documentation](./api/README.md)

### 2. GraphQL API

**Framework**: Strawberry (current) + Graphene (Legacy, DEPRECATED)

**Location**:
- Strawberry: `src/ai/backend/manager/api/gql/`
- Graphene (Legacy): `src/ai/backend/manager/models/gql_models/`

**Related Documentation**:
- [GraphQL API (Strawberry)](./api/gql/README.md)
- [Legacy GraphQL (Graphene)](./models/gql_models/README.md) - DEPRECATED

### 3. Event Dispatcher

**Framework**: Backend.AI Event Dispatcher

**Location**: `src/ai/backend/common/events/`

**Event Types**:
- **Broadcast Events**: Received by all Manager instances
- **Anycast Events**: Received by only one Manager instance

**Processing Flow**:
```
Event Producer → Event Dispatcher → Event Handler → Service
```

**Related Documentation**: [Event Dispatcher System](../common/events/README.md)

### 4. Background Task Handler

**Framework**: Backend.AI Background Task Handler

**Location**: `src/ai/backend/common/bgtask/`

**Purpose**:
Handles long-running tasks asynchronously. Issues Task IDs that allow clients to subscribe to progress updates or results via events.

**Processing Flow**:
```
Task Request → Background Task Handler → Task Execute → Event Notification
```

**Related Documentation**: [Background Task Handler System](../common/bgtask/README.md)

### Entry Point Interactions

Each entry point operates independently, but service logic can trigger background tasks or publish events as needed.

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
Sessions represent user compute requests and are composed of one or more kernels:
- **Session ID**: Unique identifier for the session
- **Access Key**: Owner's API access key
- **Status**: Session state (PENDING, RUNNING, TERMINATED, etc.)
- **Resource Allocation**: Allocated CPU, memory, GPU resources
- **Cluster Size**: Number of kernels in multi-container mode

Session Lifecycle:
1. User creates session via API
2. Manager schedules and allocates resources
3. Agent creates and starts kernel containers
4. User executes code and uses services
5. Session terminates (user request or timeout)
6. Resources are returned to the pool

### Agents
Agents are compute node workers that execute kernels:
- **Agent ID**: Unique identifier for the agent
- **Status**: Agent state (ALIVE, LOST, TERMINATED)
- **Available Resources**: CPU, memory, GPU capacity
- **Occupied Slots**: Currently allocated resources
- **Scaling Group**: Group to which the agent belongs

Agent Monitoring:
- Manager periodically checks agent health
- Agent heartbeat and resource status updates
- Automatic detection of lost agents
- Kernel rebalancing during failures

### Scaling Groups
Scaling groups manage agent clusters logically:
- **Group Name**: Unique identifier for the scaling group
- **Scheduler Type**: Scheduling algorithm (FIFO, LIFO, DRF, etc.)
- **Agent Members**: Agents belonging to the group
- **Allowed vFolder Hosts**: Permitted storage backends
- **Resource Limits**: Per-group resource limits

### Virtual Folders (VFolders)
VFolders provide persistent storage:
- **Folder Name**: User-defined folder name
- **Host**: Storage backend location
- **Ownership**: User or group ownership
- **Permissions**: Read/write permissions
- **Quota**: Storage capacity limit

## Infrastructure Dependencies

### Required Infrastructure

#### PostgreSQL (Persistent Data)
- **Purpose**:
  - Store all Backend.AI metadata
  - User/Group/Domain information
  - Session and kernel history
  - VFolder metadata
  - Resource allocation records
- **Halfstack Port**: 8101 (host) → 5432 (container)
- **Key Tables**:
  - `users`, `keypairs` - User credentials
  - `groups`, `domains` - Organization structure
  - `kernels`, `sessions` - Session information
  - `agents` - Agent status
  - `vfolders` - VFolder metadata
  - `scaling_groups` - Scaling group configuration

#### Redis (Caching and Real-time Data)
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
  - `http://localhost:18080/metrics/service_discovery` - Service discovery endpoint for automated metrics collection configuration
- **Key Metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time
  - `backendai_scheduler_enqueue_success` - Successful scheduling count
  - `backendai_agent_registry_count` - Number of agents
- **Note**: The service discovery endpoint provides automated configuration for Prometheus to discover all Backend.AI component endpoints

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

**Redis Settings**:
- Redis connection information
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

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

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

The Manager component exposes Prometheus metrics at the `/metrics` endpoint for monitoring system health and performance.

#### Label Conventions

Many metrics share common labels for error tracking and classification:

**Error-related Labels** (populated only when errors occur):
- `domain`: Error domain categorizing the error source (e.g., "session", "agent", "storage")
- `operation`: Specific operation that failed (e.g., "create", "terminate", "allocate")
- `error_detail`: Detailed error information for debugging

**Status Labels**:
- `status`: Operation outcome - typically "success" or "failure"
- `success`: Boolean string ("True" or "False") indicating operation success

#### API Metrics

REST API request monitoring metrics.

**`backendai_api_request_count`** (Counter)
- **Description**: Total number of REST API requests received
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: API endpoint path (e.g., "/v1/session/create")
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
  - `status_code`: HTTP response status code (200, 400, 500, etc.)

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
  - `event_type`: Type of event (e.g., "session_terminated", "kernel_started")

**`backendai_event_failure_count`** (Counter)
- **Description**: Number of failed event processing attempts
- **Labels**:
  - `event_type`: Type of event that failed
  - `exception`: Exception class name (e.g., "SessionNotFound", "AgentError")
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
  - `task_name`: Background task identifier (e.g., "recalc_agent_resource_occupancy")

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
  - `entity_type`: Type of entity being operated on (e.g., "session", "kernel", "agent")
  - `operation_type`: Type of operation (e.g., "create", "terminate", "restart")
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
  - `layer`: Specific layer (e.g., "session_repository", "agent_client", "valkey_live")
  - `operation`: Operation name (e.g., "fetch_session", "create_kernel")

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
- **Description**: CPU usage percentage of the Manager process
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
  - `status`: Session status being cleaned (e.g., "TERMINATED", "ERROR")
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

The following examples demonstrate common Prometheus queries for Manager metrics. Note that Counter metrics use the `_total` suffix and Histogram metrics use `_bucket`, `_sum`, `_count` suffixes in actual queries.

**Important Notes:**
- When using `increase()` or `rate()` functions, the time range must be at least 2-4x longer than your Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or show incomplete data.
- Default Prometheus scrape interval is typically 15s-30s
- **Time range selection trade-offs**:
  - Shorter ranges (e.g., `[1m]`): Detect changes faster with more granular data, but more sensitive to noise and short-term fluctuations
  - Longer ranges (e.g., `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges like `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges like `[5m]` or `[10m]`

#### API Request Rate

**API Request Rate by Endpoint**

Calculate the per-second rate of API requests grouped by endpoint and status. This shows how many requests per second each endpoint receives. Use this to identify high-traffic endpoints and monitor overall API load.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[1m])) by (method, endpoint, status_code)
```

**Failed API Requests (5xx Errors)**

Monitor failed API requests (5xx errors) to identify service issues. This helps detect when the Manager is experiencing internal errors.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"5.."}[5m])) by (endpoint)
```

#### API Request Duration

**P95 API Request Latency**

Calculate 95th percentile (P95) latency for API requests. This shows the response time that 95% of requests complete within. Use this to identify slow endpoints and set SLA targets.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups"}[5m])) by (le, endpoint)
)
```

**Average API Request Duration**

Calculate average request duration per endpoint. This provides a simple overview of typical response times.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups"}[5m])) by (endpoint)
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups"}[5m])) by (endpoint)
```

#### GraphQL Query Performance

**GraphQL Query Rate by Operation**

Monitor GraphQL query rate by operation type and field. Use this to understand which GraphQL queries are most frequently used.

```promql
sum(rate(backendai_graphql_request_count_total{service_group="$service_groups"}[5m])) by (operation_type, field_name)
```

**Failed GraphQL Queries**

Track failed GraphQL queries with error details. This helps identify problematic queries and common error patterns.

```promql
sum(rate(backendai_graphql_request_count_total{service_group="$service_groups", success="False"}[5m])) by (field_name, error_detail)
```

#### Layer Operation Performance

**P95 Redis Operation Latency**

Monitor Redis operation latency (P95) by layer and operation. This helps identify slow Redis operations that may cause bottlenecks. Exclude broadcast/stream operations as they have different performance characteristics.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="valkey", operation!~"receive_broadcast_message|read_consumer_group"}[5m])) by (le, layer, operation)
)
```

**P95 Database Repository Latency**

Monitor database repository operation latency (P95). Use this to identify slow database queries and optimize data access patterns.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="repository"}[5m])) by (le, layer, operation)
)
```

**P95 Agent RPC Call Latency**

Monitor Agent RPC call latency (P95). This shows how long it takes to communicate with compute agents.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_layer_operation_duration_sec_bucket{domain="client", layer="agent_client"}[5m])) by (le, operation)
)
```

**Failed Layer Operations**

Track failed layer operations to identify integration issues. High error rates indicate problems with external dependencies or internal bugs.

```promql
sum(rate(backendai_layer_operation_count_total{success="False"}[5m])) by (domain, layer, operation)
```

#### Background Tasks

**Currently Running Background Tasks**

Monitor currently running background tasks. Gauge metric shows real-time count of active tasks. Use this to ensure background tasks are running and detect stuck tasks.

```promql
sum(backendai_bgtask_count) by (task_name)
```

**Background Task Completion Rate**

Track background task completion rate and success/failure status. This shows how frequently tasks complete and their success rate.

```promql
sum(rate(backendai_bgtask_done_count_total[5m])) by (task_name, status)
```

**Failed Background Tasks**

Monitor failed background tasks with error details. Use this to identify recurring task failures and debug issues.

```promql
sum(rate(backendai_bgtask_done_count_total{status="failure"}[5m])) by (task_name, error_detail)
```

#### Event Processing

**Event Processing Rate by Type**

Monitor event processing rate by event type. This shows how many events are being processed per second. Use this to understand event throughput and detect processing delays.

```promql
sum(rate(backendai_event_count_total[5m])) by (event_type)
```

**Event Processing Failures**

Track event processing failures by exception type. This helps identify problematic event handlers and common error patterns.

```promql
sum(rate(backendai_event_failure_count[5m])) by (event_type, exception)
```

**P95 Event Processing Duration**

Calculate P95 event processing duration. This shows how long it takes to process different types of events. Use this to identify slow event handlers that may cause delays.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_event_processing_time_sec_bucket[5m])) by (le, event_type)
)
```

#### Action Metrics

**Action Execution Rate**

Monitor action execution rate grouped by entity and operation type. This shows the rate of high-level business operations like session creation. Use this to understand system activity and user behavior patterns.

```promql
sum(rate(backendai_action_count_total[5m])) by (entity_type, operation_type, status)
```

**Failed Actions**

Track failed actions with detailed error information. This helps identify which operations are failing and why.

```promql
sum(rate(backendai_action_count_total{status="failure"}[5m])) by (entity_type, operation_type, error_detail)
```

**P95 Action Execution Duration**

Calculate P95 action execution duration. This shows how long key operations take to complete. Use this to set performance expectations and identify slow operations.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_action_duration_sec_bucket[5m])) by (le, entity_type, operation_type)
)
```

#### System Resources

Monitor active asyncio tasks in the event loop. High task counts may indicate resource leaks or excessive concurrency.

```promql
backendai_async_task_count
```

Monitor CPU usage percentage of the Manager process. Use this to detect CPU bottlenecks and capacity planning.

```promql
backendai_cpu_usage_percent
```

Monitor Resident Set Size (physical memory usage). This shows actual RAM usage by the Manager process.

```promql
backendai_memory_used_rss
```

Monitor Virtual Memory Size (total allocated memory). This includes swapped memory and memory-mapped files.

```promql
backendai_memory_used_vms
```

#### Session Sweeper

Monitor session cleanup operations by session status. This shows how many sessions are being cleaned up and success rate. Use this to ensure proper resource cleanup and identify cleanup issues.

```promql
sum(rate(backendai_sweep_session_count_total[5m])) by (status, success)
```

Monitor kernel cleanup operation rate. This tracks orphaned kernel cleanup operations.

```promql
sum(rate(backendai_sweep_kernel_count_total[5m])) by (success)
```

### Logs
- API request/response logs
- Session scheduling decision logs
- Resource allocation/release events
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
- **Port**: 6021 (client API), 6022 (manager API)
- **Main Operations**: VFolder management, file upload/download, file listing

### etcd Communication
- **Protocol**: gRPC (etcd v3 API)
- **Port**: 2379
- **Main Operations**: Configuration management, service discovery, watch notifications

## Development

See [README.md](./README.md) for development setup instructions.

## Manager Architecture Documentation

### Internal Architecture
- **[Sokovan Orchestration System](./sokovan/README.md)**: Session scheduling orchestrator with 3-tier architecture
  - [Scheduler](./sokovan/scheduler/README.md): Core scheduling engine for session placement and resource allocation
  - [Scheduling Controller](./sokovan/scheduling_controller/README.md): Validation and preparation logic for scheduling
  - [Deployment Controller](./sokovan/deployment/README.md): Deployment lifecycle management
- **[Services Layer](./services/README.md)**: Business logic patterns, design principles, and implementation guidelines
- **[Repositories Layer](./repositories/README.md)**: Data access patterns, query optimization, and transaction management
- **[Actions Layer](./actions/README.md)**: Permission validation, monitoring, and request handling

### Related Components
- [Agent Component](../agent/README.md): Kernel lifecycle management on compute nodes
- [Storage Proxy Component](../storage/README.md): Virtual folder and storage backend management
- [Webserver Component](../web/README.md): Web UI hosting and session management
- [Overall Architecture](../README.md): System-wide architecture and component interactions
