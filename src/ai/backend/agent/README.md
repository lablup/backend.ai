# Backend.AI Agent

## Purpose

The Agent is a compute node component responsible for container lifecycle management. It runs computing sessions as containers, monitors resource usage, and reports status to the Manager.

## Key Responsibilities

### 1. Container Lifecycle Management
- Create and start containers from session specifications
- Initialize kernels and execute runtime configuration
- Monitor container health and status
- Delete containers upon session termination
- Handle container restarts and error recovery

### 2. Resource Monitoring
- Track CPU, memory, GPU usage per container
- Monitor disk I/O and network traffic
- Collect accelerator metrics (CUDA, ROCm, TPU)
- Report resource availability to Manager
- Enforce resource limits via cgroups

### 3. Local Storage Management
- Manage scratch storage for temporary files
- Mount virtual folders (vfolders) to containers
- Handle file permissions and ownership
- Clean up storage after session termination

### 4. Service Port Management
- Expose container service ports (Jupyter, SSH, TensorBoard, etc.)
- Forward traffic from App Proxy to containers
- Manage port allocation from configured ranges
- Handle SSL/TLS termination when needed

### 5. Agent Status Reporting
- Periodically report agent status to Manager
- Send heartbeat signals indicating availability
- Update occupied and available resource slots
- Report errors and exceptional conditions

## Entry Points

Agent has 4 entry points. The RPC Server handles Manager requests, Event Dispatcher sends and receives events, Background Task Handler performs async tasks, and Internal REST API is used exclusively for metrics exposure.

### 1. RPC Server (Primary Request Handler)

**Framework**: Callosum (ZeroMQ-based RPC, Curve authentication)

**Port**: 6011 (default)

**Key Features**:
- Only Manager can send RPC requests to Agent (no direct user access)

### 2. Event Dispatcher

**System**: Backend.AI Event Dispatcher

Agent sends Agent and Kernel lifecycle events to Manager.

**Published Events**: Agent and Kernel lifecycle events

**Consumed Events**: Plugin integration events

**Related Documentation**: [Event Dispatcher System](../common/events/README.md)

### 3. Background Task Handler

**System**: Backend.AI Background Task Handler

Handles long-running tasks asynchronously, issues Task IDs, and notifies completion via events.

**Usage Examples**:
- Image pulling tasks
- Large-scale container cleanup tasks

**Related Documentation**: [Background Task Handler System](../common/bgtask/README.md)

### 4. Internal REST API (Metrics Only)

**Framework**: aiohttp

**Port**: 6003 (metrics only, separate from RPC port)

**Endpoints**:
- `GET /metrics` - Expose Prometheus metrics


**Key Features**:
- Metrics exposure only (no service logic triggering)
- Prometheus scrapes periodically
- Auto-registered via Manager's Service Discovery

### Entry Point Interactions

Each Entry Point operates independently. However, service logic can coordinate them:

**Background Task Triggering**:
- Service logic in RPC Server or Event Dispatcher can trigger long-running tasks as Background Tasks.

**Event Publishing**:
- RPC Server or Background Task can publish events via Event Dispatcher after task completion.

**Integrated Architecture**:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  RPC Server  │  │Event Dispatch│  │  Background  │
│   (Callosum) │  │              │  │     Task     │
│   Port 6011  │  │              │  │              │
└───────┬──────┘  └───────┬──────┘  └───────┬──────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Agent Core Logic  │
                │  - Resource Mgmt   │
                │  - Kernel Mgmt     │
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │  Container Backend │
                └────────────────────┘

        ┌──────────────────┐
        │ Internal REST API│ (Independent, metrics only)
        │   Port 6003      │
        └──────────────────┘
```

## Architecture

```
┌────────────────────────────────────────┐
│         Agent Server (agent.py)        │
├────────────────────────────────────────┤
│    Container Backend (docker/)         │  ← Docker
├────────────────────────────────────────┤
│      Resource Monitor (stats.py)       │  ← CPU, GPU, Memory
├────────────────────────────────────────┤
│   Storage Manager (scratch.py fs.py)   │  ← Local and mounted storage
├────────────────────────────────────────┤
│      Plugin System (plugin/)           │  ← Plugin
└────────────────────────────────────────┘
```

## Directory Structure

```
agent/
├── docker/              # Docker container backend
│   ├── agent.py        # Docker-specific agent implementation
│   └── resources.py    # Docker resource management
├── watcher/             # Agent watcher
├── plugin/              # Plugin system
├── observer/            # Metrics observers
├── cli/                 # CLI commands
├── config/              # Configuration
├── agent.py             # Main agent logic
├── server.py            # RPC server entry point
├── kernel.py            # Kernel (container) management
├── resources.py         # Resource allocation
├── stats.py             # Statistics aggregation
├── scratch.py           # Scratch storage management
└── fs.py                # Filesystem utilities
```

## Core Concepts

### Kernels
Kernels represent running containers executing computing sessions:
- **Kernel ID**: Unique identifier for the container
- **Session ID**: Associated session in Manager
- **Image**: Container image (e.g., `lablup/python:3.11-ubuntu20.04`)
- **Resources**: Allocated CPU, memory, GPU slots
- **Status**: PREPARING, RUNNING, RESTARTING, TERMINATING, TERMINATED
- **Service Ports**: Exposed ports for services (Jupyter, SSH, etc.)

### Container Backend
The Agent supports multiple container runtimes:
- **Docker**: Standard Docker containers

The Docker backend implements these interfaces:
- `create_kernel()`: Create new container
- `destroy_kernel()`: Remove container
- `restart_kernel()`: Restart container
- `get_kernel_status()`: Query container status
- `execute_code()`: Execute code in container

### Resource Allocation
Resources are allocated from the agent's capacity:
- **CPU Slots**: Measured in cores (e.g., 2.0 cores)
- **Memory Slots**: Measured in bytes (e.g., 4GB)
- **GPU Slots**: Number of GPU devices (e.g., 1 GPU)
- **Accelerator Slots**: Custom accelerator resources

The Agent tracks:
- **Total Capacity**: Maximum available resources
- **Occupied Slots**: Currently allocated resources
- **Available Slots**: Remaining resources for new sessions

### Scratch Storage
Each kernel receives local scratch storage:
- **Location**: `/scratches/{kernel_id}`
- **Quota**: Configurable size limit per kernel
- **Cleanup**: Automatically removed after kernel termination

### Virtual Folder Mounting
VFolders are mounted to containers at runtime:
- **Mount Point**: `/home/work/{vfolder_name}`
- **Permissions**: RO, RW, or RW-DELETE
- **Backend**: Storage Proxy manages actual storage

## Resource Monitoring

### CPU Monitoring
- Track per-container CPU usage via cgroups
- Measure CPU time in user and system modes
- Calculate CPU utilization percentages
- Enforce CPU quotas and limits

### Memory Monitoring
- Track RSS (Resident Set Size) per container
- Measure cache and swap usage
- Detect OOM (Out-of-Memory) conditions
- Enforce memory limits via cgroups

### Shared Memory (shmem)
Containers can request shared memory (`/dev/shm`) for inter-process communication.

**Docker Memory Architecture**:
- shm (tmpfs) and app memory share the Memory cgroup space
- shm has an additional ShmSize limit (tmpfs maximum size)
- Effective shm limit = `min(ShmSize, Memory cgroup available space)`

**OOM Conditions**:
| Signal | Exit Code | Condition |
|--------|-----------|-----------|
| SIGKILL | 137 | shm + app > Memory cgroup limit |
| SIGBUS | 135 | shm > ShmSize |

**Configuration**:
- Set via `resource_opts.shmem` in session specification
- Docker HostConfig: `ShmSize` parameter

**References**:
- [Linux Kernel cgroup v1 Memory](https://docs.kernel.org/admin-guide/cgroup-v1/memory.html) - tmpfs/shm charged to cgroup
- [Linux Kernel cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) - shmem in memory.stat

### GPU Monitoring
- Query NVIDIA GPUs via NVML (nvidia-ml-py)
- Query AMD GPUs via ROCm SMI
- Track GPU utilization and memory usage
- Measure GPU temperature and power consumption

### Disk I/O Monitoring
- Track read/write operations per container
- Measure I/O bandwidth usage
- Monitor disk space consumption
- Enforce I/O throttling when configured

## Plugin System

Agent can uses plugin system for accelerator support:

### CUDA Plugin
- Detect NVIDIA GPUs via `nvidia-smi`
- Allocate GPU devices to containers
- Set `CUDA_VISIBLE_DEVICES` environment variable
- Monitor GPU metrics via NVML

### ROCm Plugin
- Detect AMD GPUs via `rocm-smi`
- Allocate GPU devices to containers
- Set `HIP_VISIBLE_DEVICES` environment variable
- Monitor GPU metrics via ROCm

### TPU Plugin
- Detect Google TPUs
- Configure TPU access for TensorFlow
- Monitor TPU utilization

## Communication Protocols

### Manager → Agent (ZeroMQ RPC)
- **Port**: 6011 (default)
- **Protocol**: ZeroMQ request-response
- **Operations**:
  - `create_kernel`: Create new container
  - `destroy_kernel`: Terminate container
  - `restart_kernel`: Restart container
  - `execute_code`: Execute code in container
  - `get_status`: Query agent and kernel status

### Agent → Manager (HTTP Watcher API)
- **Port**: 6009 (default)
- **Protocol**: HTTP
- **Operations**:
  - Heartbeat signals
  - Resource usage reporting
  - Kernel status updates
  - Error notifications

### Agent → Storage Proxy
- **Protocol**: HTTP
- **Operations**:
  - Mount vfolder
  - Unmount vfolder
  - Query vfolder metadata

## Container Execution Flow

```
1. Manager sends create_kernel RPC
   ↓
2. Agent validates resource availability
   ↓
3. Agent pulls container image (if needed)
   ↓
4. Agent creates scratch directory
   ↓
5. Agent mounts vfolders via Storage Proxy
   ↓
6. Agent creates container with resources
   ↓
7. Agent starts container and runs init script
   ↓
8. Agent registers service ports
   ↓
9. Agent reports kernel status to Manager
   ↓
10. Container runs until termination
   ↓
11. Agent cleans up resources upon termination
```

## Service Ports

Containers can expose service ports:
- **Jupyter Notebook**: Port 8080 (HTTP)
- **Jupyter Lab**: Port 8090 (HTTP)
- **SSH**: Port 2200 (TCP)
- **TensorBoard**: Port 6006 (HTTP)
- **Custom Services**: User-defined ports

Service ports are:
- **Allocated** from configured range (default 30000-31000)
- **Registered** with App Proxy for external access
- **Forwarded** from agent host to container
- **Cleaned up** upon container termination

## Configuration

See `configs/agent/halfstack.toml` for configuration file examples.

### Key Configuration Items

**Agent Basic Settings**:
- Agent ID and region information
- Resource slot definitions
- Container runtime configuration (Docker)

**Storage Settings**:
- Scratch storage root path
- Per-session quota

**Service Port Settings**:
- Container port range

**Resource Monitoring**:
- Watcher interval settings

## Infrastructure Dependencies

### Required Infrastructure

#### Container Runtime
- **Purpose**: Container creation and management
- **Supported Runtimes**: Docker

#### Redis (Event and State Management)
- **Purpose**:
  - Send heartbeat events (for Manager registration)
  - Update agent status
  - Manage background tasks
- **Note**: Agent registers with Manager via Redis and receives RPC commands from Manager.

#### Manager Connection
- **Protocol**: ZeroMQ RPC (6011), HTTP Watcher API (6009)
- **Purpose**: Receive session commands from Manager, report status
- **Note**: Agent only receives commands from Manager, not directly from users or other components.

#### etcd (Global Configuration)
- **Purpose**:
  - Retrieve global configuration (storage volumes, etc.)
  - Auto-discover Manager address

### Optional Infrastructure (Observability)

Optional infrastructure for Agent monitoring.

#### Prometheus (Metrics Collection)
- **Purpose**:
  - Monitor agent resource utilization
  - Collect kernel (container) metrics
  - Track heartbeat and health status
- **HTTP Service Port**: 6003 (separate from RPC port 6011)
- **Exposed Endpoint**: `http://localhost:6003/metrics`
- **Key Metrics**:
  - `backendai_agent_heartbeat` - Last heartbeat timestamp
  - `backendai_agent_cpu_usage` - CPU usage percentage
  - `backendai_agent_mem_usage` - Memory usage (bytes)
  - `backendai_agent_gpu_usage` - GPU usage percentage
  - `backendai_kernel_count` - Number of running kernels
- **Service Discovery**: Automatically registered via Manager's HTTP SD
  - Agent auto-registers with Manager at startup
  - Manager provides agent information to Prometheus SD

#### Loki (Log Aggregation)
- **Purpose**:
  - Centralized agent log collection
  - Aggregate kernel execution logs
  - Track errors and debugging information
- **Log Transmission Methods**:
  - Direct HTTP API usage
  - Use Promtail or Fluent Bit
- **Log Labels**:
  - `agent_id` - Agent identifier
  - `kernel_id` - Kernel identifier
  - `level` - Log level

#### Container Runtime Metrics
- **Docker**: Container metrics via cAdvisor or Docker API
- **cgroups**: Direct cgroups filesystem reading

### Container Runtime Requirements

#### Docker
- **Minimum Version**: Docker 20.10+
- **Required Features**:
  - cgroups v2 support (resource limits)
  - GPU support (NVIDIA Docker Runtime or CDI)

### Storage Requirements

#### Local Scratch Storage
- **Purpose**: Temporary files, build cache
- **Recommended Specifications**:
  - Fast SSD (NVMe recommended)
  - Minimum 100GB free space
  - Configurable per-session quota

#### VFolder Mount
- **Dependencies**: Storage Proxy or direct storage access
- **Recommendations**:
  - High-performance network (10GbE or higher)
  - Low-latency storage

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Agent
./backend.ai ag start-server
```

#### Observability Integration
Agent automatically registers with Prometheus via Manager's Service Discovery.

## Metrics and Monitoring

### Prometheus Metrics
Agent exposes metrics:

#### RPC Related Metrics
Metrics related to processing RPC commands received from Manager.

**`backendai_rpc_requests`** (Counter)
- **Description**: Total RPC requests processed by the agent
- **Labels**:
  - `method`: RPC method name (e.g., "create_kernel", "destroy_kernel", "execute_code")
- Tracks processing frequency by Manager command type

**`backendai_rpc_failure_requests`** (Counter)
- **Description**: Failed RPC request count
- **Labels**:
  - `method`: RPC method name that failed
  - `exception`: Exception class name (e.g., "ContainerNotFound", "ResourceExhausted")
- Analyzes RPC command processing failure causes

**`backendai_rpc_request_duration_seconds`** (Histogram)
- **Description**: RPC request processing time in seconds
- **Labels**:
  - `method`: RPC method name
- **Buckets**: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30, 60] seconds
- Measures performance of RPC commands like kernel creation/deletion

#### Resource Utilization Metrics
Metrics related to container and hardware resource usage.

**`backendai_container_utilization`** (Gauge)
- **Description**: Container resource utilization per kernel
- **Labels**:
  - `container_metric_name`: Metric type (cpu_used, cpu_util, mem, cuda_mem, cuda_util, net_rx, net_tx)
  - `agent_id`: Agent identifier
  - `kernel_id`: Kernel identifier (Backend.AI's container wrapper, not the actual container ID)
  - `session_id`: Session identifier
  - `user_id`: User UUID who owns the session
  - `project_id`: Project UUID that the session belongs to
  - `value_type`: Value interpretation (current, capacity, pct)
- Tracks resource usage per kernel (CPU, memory, GPU, network, etc.)

**`backendai_device_utilization`** (Gauge)
- **Description**: Physical device utilization on the agent node
- **Labels**:
  - `device_metric_name`: Metric type (cpu_util, mem, cuda_mem, cuda_util, cuda_temp, cuda_power)
  - `agent_id`: Agent identifier
  - `device_id`: Hardware device identifier (e.g., GPU index)
  - `value_type`: Value interpretation (current, capacity, pct)
- Tracks hardware device usage (GPU, CPU, memory) on the agent node

#### Container Lifecycle Synchronization Metrics
Metrics related to container state synchronization operations between Manager and Agent.

**`backendai_sync_container_lifecycle_trigger_count`** (Counter)
- **Description**: Number of times container lifecycle sync was triggered
- **Labels**:
  - `agent_id`: Agent identifier
- Frequency of container state synchronization between Manager and Agent

**`backendai_sync_container_lifecycle_success_count`** (Counter)
- **Description**: Number of successfully synchronized containers
- **Labels**:
  - `agent_id`: Agent identifier
- Number of successfully synchronized kernels

**`backendai_sync_container_lifecycle_failure_count`** (Counter)
- **Description**: Number of failed container synchronization attempts
- **Labels**:
  - `agent_id`: Agent identifier
  - `exception`: Exception class name causing the failure
- Tracks synchronization failure causes

#### Statistics Collection Task Metrics
Metrics related to node, container, and process level statistics collection.

**`backendai_stat_task_trigger_count`** (Counter)
- **Description**: Number of times statistics collection was triggered
- **Labels**:
  - `agent_id`: Agent identifier
  - `stat_scope`: Statistics scope (node, container, process)
- Collection frequency by Node/Container/Process level

**`backendai_stat_task_success_count`** (Counter)
- **Description**: Number of successful statistics collection operations
- **Labels**:
  - `agent_id`: Agent identifier
  - `stat_scope`: Statistics scope (node, container, process)
- Tracks statistics collection success rate

**`backendai_stat_task_failure_count`** (Counter)
- **Description**: Number of failed statistics collection operations
- **Labels**:
  - `agent_id`: Agent identifier
  - `stat_scope`: Statistics scope (node, container, process)
  - `exception`: Exception class name causing the failure
- Analyzes statistics collection failure causes

### Prometheus Query Examples

The following examples demonstrate common Prometheus queries for Agent metrics. Note that Counter metrics use the `_total` suffix and Histogram metrics use `_bucket`, `_sum`, `_count` suffixes in actual queries.

**Important Notes:**
- When using `increase()` or `rate()` functions, the time range must be at least 2-4x longer than your Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or show incomplete data.
- Default Prometheus scrape interval is typically 15s-30s
- **Time range selection trade-offs**:
  - Shorter ranges (e.g., `[1m]`): Detect changes faster with more granular data, but more sensitive to noise and short-term fluctuations
  - Longer ranges (e.g., `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges like `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges like `[5m]` or `[10m]`

#### RPC Request Monitoring

**RPC Request Rate by Method**

Monitor RPC request rate by method. This shows how frequently the Manager sends commands to agents. Use this to understand agent workload and command distribution.

```promql
sum(rate(backendai_rpc_requests_total{service_group="$service_groups"}[5m])) by (method)
```

**RPC Failure Rate by Method**

Track RPC failure rate by method and exception type. This helps identify which RPC operations are failing and why.

```promql
sum(rate(backendai_rpc_failure_requests_total{service_group="$service_groups"}[5m])) by (method, exception)
```

**P95 RPC Request Duration**

Calculate P95 RPC request duration by method. This shows how long critical operations like kernel creation take. Use this to identify performance bottlenecks in agent operations.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_rpc_request_duration_seconds_bucket{service_group="$service_groups"}[5m])) by (le, method)
)
```

#### Container Resource Utilization

**Top 5 GPU Memory Usage by Kernel**

Monitor GPU memory usage by kernel (top 5). This identifies kernels consuming the most GPU memory. Note: `topk` returns the top N items at each evaluation time. Over multiple time points, you may see more than 5 unique kernels if different kernels appear in the top 5 at different times.

```promql
topk(5, sum(backendai_container_utilization{container_metric_name="cuda_mem", value_type="current"}) by (kernel_id))
```

**Top 5 GPU Utilization by Kernel**

Monitor GPU utilization by kernel (top 5). This shows which kernels are actively using GPU compute. Note: `topk` returns the top N items at each evaluation time. Over multiple time points, you may see more than 5 unique kernels if different kernels appear in the top 5 at different times.

```promql
topk(5, sum(backendai_container_utilization{container_metric_name="cuda_util", value_type="current"}) by (kernel_id))
```

**Top 5 CPU Utilization Increase by Kernel**

Track CPU utilization increase rate by kernel (top 5). This shows CPU consumption trends over time. Note: Divided by 1000 to convert from per-mille to percentage. `topk` returns the top N items at each evaluation time. Over multiple time points, you may see more than 5 unique kernels if different kernels appear in the top 5 at different times.

```promql
topk(5, sum(increase(backendai_container_utilization{container_metric_name="cpu_util", value_type="current"}[5m])) by (kernel_id)) / 1000
```

**Network RX Traffic by Kernel**

Monitor network RX (receive) traffic by kernel. This tracks inbound network bandwidth usage per container.

```promql
sum(increase(backendai_container_utilization{container_metric_name="net_rx", value_type="current"}[5m])) by (kernel_id)
```

**Network TX Traffic by Kernel**

Monitor network TX (transmit) traffic by kernel. This tracks outbound network bandwidth usage per container.

```promql
sum(increase(backendai_container_utilization{container_metric_name="net_tx", value_type="current"}[5m])) by (kernel_id)
```

#### Device Utilization (Agent-level)

**GPU Memory Usage by Agent**

Monitor GPU memory usage at the agent level. This shows total GPU memory consumption on each agent node.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_mem", value_type="current"}) by (agent_id)
```

**GPU Memory Capacity by Agent**

Monitor GPU memory capacity. This shows the maximum available GPU memory on each agent.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_mem", value_type="capacity"}) by (agent_id)
```

**GPU Utilization Percentage by Agent**

Monitor GPU utilization percentage at the agent level. This shows overall GPU usage across all kernels on the agent.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_util", value_type="current"}) by (agent_id)
```

**CPU Utilization Increase by Agent**

Track CPU utilization increase rate at the agent level. This shows agent-wide CPU consumption trends.

```promql
sum(increase(backendai_device_utilization{device_metric_name="cpu_util", value_type="current"}[5m])) by (agent_id) / 1000
```

**Network RX Traffic by Agent**

Monitor network RX (receive) traffic at the agent level. This tracks total inbound network bandwidth usage on each agent node.

```promql
sum(increase(backendai_device_utilization{device_metric_name="net_rx", value_type="current"}[5m])) by (agent_id)
```

**Network TX Traffic by Agent**

Monitor network TX (transmit) traffic at the agent level. This tracks total outbound network bandwidth usage on each agent node.

```promql
sum(increase(backendai_device_utilization{device_metric_name="net_tx", value_type="current"}[5m])) by (agent_id)
```

#### Container Lifecycle Synchronization

**Container Sync Trigger Frequency**

Monitor container sync trigger frequency. This shows how often the agent synchronizes container state with the Manager.

```promql
sum(rate(backendai_sync_container_lifecycle_trigger_count_total[5m])) by (agent_id)
```

**Container Sync Success Rate**

Track container sync success rate. This helps ensure containers are properly synchronized.

```promql
sum(rate(backendai_sync_container_lifecycle_success_count_total[5m])) by (agent_id)
```

**Container Sync Failure Rate**

Monitor container sync failures. This identifies issues with container state synchronization.

```promql
sum(rate(backendai_sync_container_lifecycle_failure_count_total[5m])) by (agent_id, exception)
```

#### Statistics Collection

**Statistics Collection Trigger Rate**

Monitor statistics collection trigger rate by scope. This shows how frequently statistics are collected at different levels.

```promql
sum(rate(backendai_stat_task_trigger_count_total[5m])) by (agent_id, stat_scope)
```

**Statistics Collection Success Rate**

Track statistics collection success rate. This ensures statistics collection is working properly.

```promql
sum(rate(backendai_stat_task_success_count_total[5m])) by (agent_id, stat_scope)
```

**Statistics Collection Failure Rate**

Monitor statistics collection failures. This identifies issues with resource monitoring.

```promql
sum(rate(backendai_stat_task_failure_count_total[5m])) by (agent_id, stat_scope, exception)
```

### Logs
Agent logs include:
- Kernel creation and termination events
- Resource allocation and release
- Error situations and recovery operations
- RPC request/response tracking

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Manager Component](../manager/README.md) - Session orchestration
- [Storage Proxy Component](../storage/README.md) - Virtual folder management
- [Overall Architecture](../README.md) - System-wide architecture
