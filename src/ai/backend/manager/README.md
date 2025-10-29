# Backend.AI Manager

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

## Architecture

```
┌───────────────────────────────────────────┐
│              API Layer                    │
│  - REST API Handler (Starlette)           │
│  - GraphQL Handler (GraphQL Core)         │
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
│  - Domain Types & DTOs                    │
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
│   ├── session.py      # Session data access
│   ├── agent.py        # Agent data access
│   ├── user.py         # User data access
│   └── ...
├── services/            # Business logic layer
│   ├── scheduler/      # Session scheduling service
│   ├── session/        # Session lifecycle management
│   ├── quota/          # Resource quota management
│   └── ...
├── api/                 # API handlers and routes
│   ├── rest.py         # REST API endpoints
│   ├── graphql.py      # GraphQL schema and resolvers
│   ├── auth.py         # Authentication handlers
│   └── ...
├── config/              # Configuration management
│   ├── sample.toml     # Sample configuration
│   └── ...
├── cli/                 # CLI commands
│   ├── schema.py       # Database schema management
│   ├── fixture.py      # Test data management
│   └── ...
├── clients/             # External service clients
│   ├── agent.py        # Agent RPC client
│   ├── storage.py      # Storage proxy client
│   └── ...
├── scheduler/           # Scheduling algorithms and logic
│   ├── dispatcher.py   # Scheduling dispatcher
│   ├── predicates.py   # Scheduling predicates
│   └── ...
├── events.py            # Event definitions and processing
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
- **Key Patterns**:
  - `keypair.{access_key}` - Access key information cache
  - `manager.heartbeat` - Manager heartbeat
  - `ratelimit.{identifier}` - Rate limiting counters
  - `lock.{resource}` - Distributed lock keys

#### etcd (Global Configuration)
- **Purpose**:
  - Store cluster-wide configuration
  - Service discovery
  - Agent registration
  - Dynamic configuration updates
- **Halfstack Port**: 8121 (host) → 2379 (container)
- **Key Prefixes**:
  - `config/` - Global configuration
  - `nodes/manager` - Manager node information
  - `volumes/` - VFolder host configuration

### Optional Infrastructure (Observability)

#### Prometheus (Metrics Collection)
- **Purpose**:
  - API request metrics
  - Session scheduling metrics
  - Resource usage metrics
  - Background task metrics
- **Exposed Endpoint**: `http://localhost:8091/metrics`
- **Key Metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time
  - `backendai_scheduler_enqueue_success` - Successful scheduling count
  - `backendai_agent_registry_count` - Number of agents

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
- Key expiration time

**etcd Settings**:
- etcd endpoint addresses
- Configuration key prefixes
- Watch settings

**API Settings**:
- Listen address and port
- CORS configuration
- Rate limiting settings
- Authentication method

**Scheduling Settings**:
- Default scheduler type
- Scheduling interval
- Resource allocation policy

**Session Settings**:
- Session timeout
- Maximum session duration
- Container creation timeout

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Initialize database
./backend.ai mgr schema oneshot

# Populate sample data
./backend.ai mgr fixture populate sample-configs/example-keypairs.json
./backend.ai mgr fixture populate sample-configs/example-resource-presets.json

# Start Manager
./backend.ai mgr start-server
```

#### API Access
- REST API: http://localhost:8081
- GraphQL API: http://localhost:8081/graphql
- Admin GraphQL UI: http://localhost:8081/graphql-ui

## Metrics and Monitoring

### Prometheus Metrics

#### API Metrics
Metrics related to API request processing.

- `backendai_api_request_count`: Total API requests
  - Labels: method, endpoint, domain, operation, error_detail, status_code
  - Tracks REST API and GraphQL request counts

- `backendai_api_request_duration_sec`: API request processing time (seconds)
  - Labels: method, endpoint, domain, operation, error_detail, status_code
  - Measures API response time

#### GraphQL Metrics
Metrics related to GraphQL query processing.

- `backendai_graphql_query_count`: Total GraphQL queries
  - Labels: query_name, domain, operation, error_detail, status_code

- `backendai_graphql_query_duration_sec`: GraphQL query processing time (seconds)
  - Labels: query_name, domain, operation, error_detail, status_code

#### Event Metrics
Metrics related to event processing.

- `backendai_event_producer_count`: Event production count
  - Labels: event_name, status
  - Tracks successful/failed event production

- `backendai_event_consumer_count`: Event consumption count
  - Labels: event_name, status
  - Tracks event processing in consumers

#### Background Task Metrics
Metrics for background task execution.

- `backendai_background_task_count`: Background task execution count
  - Labels: task_name, status
  - Tracks cron jobs and periodic tasks

- `backendai_background_task_duration_sec`: Background task execution time (seconds)
  - Labels: task_name, status

#### Action Metrics
Metrics for specific actions and business logic.

- `backendai_action_execution_count`: Action execution count
  - Labels: action_name, status
  - Tracks session creation, termination, and other major actions

- `backendai_action_execution_duration_sec`: Action execution time (seconds)
  - Labels: action_name, status

#### Layer Operation Metrics
Metrics for operations at each architecture layer.

- `backendai_layer_operation_count`: Operation count per layer
  - Labels: layer (api/service/repository), operation_name, status

- `backendai_layer_operation_duration_sec`: Operation time per layer (seconds)
  - Labels: layer, operation_name, status

#### System Metrics
System-level metrics.

- `backendai_db_connection_pool_size`: Database connection pool size
  - Current active connections

- `backendai_db_connection_pool_overflow`: Connection pool overflow count
  - Number of connections exceeding pool limit

- `backendai_redis_connection_count`: Redis connection count
  - Current active Redis connections

#### Event Propagator Metrics
Metrics for event propagation to external systems.

- `backendai_event_propagator_webhook_count`: Webhook call count
  - Labels: event_type, status

- `backendai_event_propagator_webhook_duration_sec`: Webhook call time (seconds)
  - Labels: event_type, status

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
- **Main Operations**:
  - `create_kernel`: Create kernel
  - `destroy_kernel`: Destroy kernel
  - `restart_kernel`: Restart kernel
  - `execute_code`: Execute code
  - `upload_file`: File upload
  - `download_file`: File download
  - `get_container_stats`: Get container resource usage

### Storage Proxy Communication
- **Protocol**: HTTP/gRPC
- **Port**: 6021 (client API), 6022 (manager API)
- **Main Operations**:
  - `create_vfolder`: Create VFolder
  - `delete_vfolder`: Delete VFolder
  - `upload_file`: Upload file to VFolder
  - `download_file`: Download file from VFolder
  - `list_files`: List VFolder files

### etcd Communication
- **Protocol**: gRPC (etcd v3 API)
- **Port**: 2379
- **Main Operations**:
  - `get`: Get configuration values
  - `put`: Set configuration values
  - `watch`: Watch configuration changes
  - `lease`: Manage service registration

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Session Scheduling](./scheduler/README.md) - Session scheduling algorithms and policies
- [Agent Component](../agent/README.md) - Agent component
- [Storage Proxy Component](../storage/README.md) - Storage proxy component
- [Overall Architecture](../README.md) - System-wide architecture
