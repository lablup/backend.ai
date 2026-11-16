# Backend.AI Agent

## Purpose

The Agent is a component that manages the container lifecycle on a node. It runs sessions as containers, monitors resource usage, and reports status to the manager.

## Key Responsibilities

### 1. Container Lifecycle Management
- Create and start containers from session specifications
- Initialize kernels and apply runtime configuration
- Monitor container health and status
- Delete containers when a session terminates
- Handle container restarts and error recovery

### 2. Resource Monitoring
- Track CPU, memory, and GPU usage per container
- Monitor disk I/O and network traffic
- Collect accelerator metrics (CUDA, ROCm, TPU)
- Report resource availability to the manager
- Enforce resource limits through cgroups

### 3. Local Storage Management
- Manage scratch storage for temporary files
- Mount vfolders to containers
- Handle file permissions and ownership
- Clean up storage when a session terminates

### 4. Service Port Management
- Expose container service ports (Jupyter, SSH, TensorBoard, and others)
- Forward traffic from the app proxy to containers
- Manage port allocation from configured ranges
- Handle SSL/TLS termination when needed

### 5. Agent Status Reporting
- Periodically report agent status to the manager
- Send agent heartbeats that indicate availability
- Update occupied and available resource slots
- Report errors and exceptional conditions

## Entry Points

The Agent has four entry points. The RPC Server handles manager requests, the Event Dispatcher sends and receives events, the Background Task Handler runs asynchronous tasks, and the Internal REST API serves metrics only.

### 1. RPC Server (Primary Request Handler)

**Framework**: Callosum (ZeroMQ-based RPC, Curve authentication)

**Port**: 6011 (default)

**Key Features**:
- The manager is the only client that sends RPC requests to the Agent. Users do not access the Agent directly.

### 2. Event Dispatcher

**System**: Backend.AI Event Dispatcher

The Agent sends Agent and Kernel lifecycle events to the manager.

**Published Events**: Agent and Kernel lifecycle events

**Consumed Events**: Plugin integration events

**Related documents**: [Event Dispatcher System](../common/events/README.md)

### 3. Background Task Handler

**System**: Backend.AI Background Task Handler

It handles long-running tasks asynchronously, issues a task ID, and notifies completion through events.

**Usage Examples**:
- Image pulling tasks
- Large-scale container cleanup tasks

**Related documents**: [Background Task Handler System](../common/bgtask/README.md)

### 4. Internal REST API (Metrics Only)

**Framework**: aiohttp

**Port**: 6003 (metrics only, separate from the RPC port)

**Endpoints**:
- `GET /metrics` - Expose Prometheus metrics


**Key Features**:
- Metrics exposure only. It does not trigger service logic.
- Prometheus scrapes it periodically.
- It registers automatically through the manager's service discovery.

### Entry Point Interactions

Each entry point runs independently. Service logic can coordinate them:

**Background Task Triggering**:
- Service logic in the RPC Server or the Event Dispatcher can start long-running tasks as background tasks.

**Event Publishing**:
- The RPC Server or a background task can publish events through the Event Dispatcher after the task completes.

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
Kernels are containers that run sessions:
- **Kernel ID**: Unique identifier for the container
- **Session ID**: Associated session in the manager
- **Image**: Container image (for example, `lablup/python:3.11-ubuntu20.04`)
- **Resources**: Allocated CPU, memory, and GPU slots
- **Status**: PREPARING, RUNNING, RESTARTING, TERMINATING, TERMINATED
- **Service Ports**: Exposed ports for services (Jupyter, SSH, and others)

### Container Backend
The Agent supports multiple container runtimes:
- **Docker**: Standard Docker containers

The Docker backend implements these interfaces:
- `create_kernel()`: Create a new container
- `destroy_kernel()`: Terminate a container
- `restart_kernel()`: Restart a container
- `get_kernel_status()`: Query container status
- `execute_code()`: Execute code in a container

### Resource Allocation
Resources are allocated from the agent's capacity:
- **CPU Slots**: Measured in cores (for example, 2.0 cores)
- **Memory Slots**: Measured in bytes (for example, 4GB)
- **GPU Slots**: Number of GPU devices (for example, 1 GPU)
- **Accelerator Slots**: Custom accelerator resources

The Agent tracks:
- **Total Capacity**: Maximum available resources
- **Occupied Slots**: Currently allocated resources
- **Available Slots**: Remaining resources for new sessions

### Scratch Storage
Each kernel receives local scratch storage:
- **Location**: `/scratches/{kernel_id}`
- **Quota**: Configurable size limit per kernel
- **Cleanup**: Removed automatically after kernel termination

### vfolder mounting
vfolders are mounted to containers at runtime:
- **Mount Point**: `/home/work/{vfolder_name}`
- **Permissions**: RO, RW, or RW-DELETE
- **Backend**: The storage proxy manages the actual storage

## Resource Monitoring

### CPU Monitoring
- Track per-container CPU usage through cgroups
- Measure CPU time in user and system modes
- Calculate CPU utilization percentages
- Enforce CPU quotas and limits

### Memory Monitoring
- Track RSS (Resident Set Size) per container
- Measure cache and swap usage
- Detect OOM (Out-of-Memory) conditions
- Enforce memory limits through cgroups

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
- Set through `resource_opts.shmem` in the session specification
- Docker HostConfig: `ShmSize` parameter

**References**:
- [Linux Kernel cgroup v1 Memory](https://docs.kernel.org/admin-guide/cgroup-v1/memory.html) - tmpfs/shm charged to cgroup
- [Linux Kernel cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) - shmem in memory.stat

### GPU Monitoring
- Query NVIDIA GPUs through NVML (nvidia-ml-py)
- Query AMD GPUs through ROCm SMI
- Track GPU utilization and memory usage
- Measure GPU temperature and power consumption

### Disk I/O Monitoring
- Track read/write operations per container
- Measure I/O bandwidth usage
- Monitor disk space consumption
- Enforce I/O throttling when configured

## Plugin System

The Agent uses the plugin system for accelerator support:

### CUDA Plugin
- Detect NVIDIA GPUs through `nvidia-smi`
- Allocate GPU devices to containers
- Set the `CUDA_VISIBLE_DEVICES` environment variable
- Monitor GPU metrics through NVML

### ROCm Plugin
- Detect AMD GPUs through `rocm-smi`
- Allocate GPU devices to containers
- Set the `HIP_VISIBLE_DEVICES` environment variable
- Monitor GPU metrics through ROCm

### TPU Plugin
- Detect Google TPUs
- Configure TPU access for TensorFlow
- Monitor TPU utilization

## Communication Protocols

### manager → Agent (ZeroMQ RPC)
- **Port**: 6011 (default)
- **Protocol**: ZeroMQ request-response
- **Operations**:
  - `create_kernel`: Create a new container
  - `destroy_kernel`: Terminate a container
  - `restart_kernel`: Restart a container
  - `execute_code`: Execute code in a container
  - `get_status`: Query agent and kernel status

### Agent → manager (HTTP Watcher API)
- **Port**: 6009 (default)
- **Protocol**: HTTP
- **Operations**:
  - Agent heartbeat signals
  - Resource usage reporting
  - Kernel status updates
  - Error notifications

### Agent → storage proxy
- **Protocol**: HTTP
- **Operations**:
  - Mount a vfolder
  - Unmount a vfolder
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
- **Allocated** from a configured range (default 30000-31000)
- **Registered** with the app proxy for external access
- **Forwarded** from the agent host to the container
- **Cleaned up** when the container terminates

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

#### Valkey (Event and State Management)
- **Purpose**:
  - Send agent heartbeat events for manager registration
  - Update agent status
  - Manage background tasks
- The Agent registers with the manager through Valkey and receives RPC commands from the manager.

#### Manager Connection
- **Protocol**: ZeroMQ RPC (6011), HTTP Watcher API (6009)
- **Purpose**: Receive session commands from the manager and report status
- The Agent receives commands from the manager only. Users and other components do not send commands directly.

#### etcd (Global Configuration)
- **Purpose**:
  - Retrieve global configuration (such as storage volumes)
  - Auto-discover the manager address

### Optional Infrastructure (Observability)

Optional infrastructure for Agent monitoring.

#### Prometheus (Metrics Collection)
- **Purpose**:
  - Monitor agent resource utilization
  - Collect kernel (container) metrics
  - Track agent heartbeat and health status
- **HTTP Service Port**: 6003 (separate from RPC port 6011)
- **Exposed Endpoint**: `http://localhost:6003/metrics`
- **Key Metrics**:
  - `backendai_agent_heartbeat` - Last agent heartbeat timestamp
  - `backendai_agent_cpu_usage` - CPU usage percentage
  - `backendai_agent_mem_usage` - Memory usage (bytes)
  - `backendai_agent_gpu_usage` - GPU usage percentage
  - `backendai_kernel_count` - Number of running kernels
- **Service discovery**: Registered automatically through the manager's HTTP service discovery
  - The Agent registers with the manager automatically at startup.
  - The manager provides agent information to the Prometheus service discovery.

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
- **Docker**: Container metrics through cAdvisor or the Docker API
- **cgroups**: Direct reads from the cgroups filesystem

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

#### vfolder mount
- **Dependencies**: storage proxy or direct storage access
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
The Agent registers with Prometheus automatically through the manager's service discovery.

## Metrics and Monitoring

### Prometheus Metrics
The Agent exposes metrics:

#### RPC Related Metrics
Metrics for RPC commands received from the manager.

**`backendai_rpc_requests`** (Counter)
- **Description**: Total RPC requests processed by the agent
- **Labels**:
  - `method`: RPC method name (for example, "create_kernel", "destroy_kernel", "execute_code")
- Tracks processing frequency by manager command type

**`backendai_rpc_failure_requests`** (Counter)
- **Description**: Failed RPC request count
- **Labels**:
  - `method`: RPC method name that failed
  - `exception`: Exception class name (for example, "ContainerNotFound", "ResourceExhausted")
- Analyzes RPC command processing failure causes

**`backendai_rpc_request_duration_seconds`** (Histogram)
- **Description**: RPC request processing time in seconds
- **Labels**:
  - `method`: RPC method name
- **Buckets**: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30, 60] seconds
- Measures performance of RPC commands such as kernel creation and deletion

#### Resource Utilization Metrics
Metrics for container and hardware resource usage.

**`backendai_container_utilization`** (Gauge)
- **Description**: Container resource utilization per kernel
- **Labels**:
  - `container_metric_name`: Metric type (cpu_used, cpu_util, mem, cuda_mem, cuda_util, net_rx, net_tx)
  - `agent_id`: Agent identifier
  - `kernel_id`: Kernel identifier (Backend.AI's container wrapper, not the actual container ID)
  - `session_id`: Session identifier
  - `user_id`: User UUID that owns the session
  - `project_id`: Project UUID that the session belongs to
  - `value_type`: Value interpretation (current, capacity, pct)
- Tracks resource usage per kernel (CPU, memory, GPU, network, and others)

**`backendai_device_utilization`** (Gauge)
- **Description**: Physical device utilization on the agent node
- **Labels**:
  - `device_metric_name`: Metric type (cpu_util, mem, cuda_mem, cuda_util, cuda_temp, cuda_power)
  - `agent_id`: Agent identifier
  - `device_id`: Hardware device identifier (for example, GPU index)
  - `value_type`: Value interpretation (current, capacity, pct)
- Tracks hardware device usage (GPU, CPU, memory) on the agent node

#### Container Lifecycle Synchronization Metrics
Metrics for container state synchronization between the manager and the Agent.

**`backendai_sync_container_lifecycle_trigger_count`** (Counter)
- **Description**: Number of times container lifecycle sync was triggered
- **Labels**:
  - `agent_id`: Agent identifier
- Frequency of container state synchronization between the manager and the Agent

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
Metrics for statistics collection at the node, container, and process levels.

**`backendai_stat_task_trigger_count`** (Counter)
- **Description**: Number of times statistics collection was triggered
- **Labels**:
  - `agent_id`: Agent identifier
  - `stat_scope`: Statistics scope (node, container, process)
- Collection frequency by node, container, and process level

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

The following examples show common Prometheus queries for Agent metrics. Counter metrics use the `_total` suffix and Histogram metrics use the `_bucket`, `_sum`, and `_count` suffixes in actual queries.

**Important Notes:**
- With `increase()` or `rate()`, the time range must be at least 2-4x the Prometheus scrape interval to get reliable data. A shorter time range can hide metrics or return incomplete data.
- The default Prometheus scrape interval is typically 15s-30s.
- **Time range trade-offs**:
  - Shorter ranges (for example, `[1m]`): Detect changes faster with more granular data, but they are more sensitive to noise and short-term fluctuations
  - Longer ranges (for example, `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges such as `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges such as `[5m]` or `[10m]`

#### RPC Request Monitoring

**RPC Request Rate by Method**

Monitor the RPC request rate by method. It shows how often the manager sends commands to agents. Use it to understand agent workload and command distribution.

```promql
sum(rate(backendai_rpc_requests_total{service_group="$service_groups"}[5m])) by (method)
```

**RPC Failure Rate by Method**

Track the RPC failure rate by method and exception type. It shows which RPC operations fail and why.

```promql
sum(rate(backendai_rpc_failure_requests_total{service_group="$service_groups"}[5m])) by (method, exception)
```

**P95 RPC Request Duration**

Calculate P95 RPC request duration by method. It shows how long critical operations such as kernel creation take. Use it to find performance bottlenecks in agent operations.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_rpc_request_duration_seconds_bucket{service_group="$service_groups"}[5m])) by (le, method)
)
```

#### Container Resource Utilization

**Top 5 GPU Memory Usage by Kernel**

Monitor GPU memory usage by kernel (top 5). It identifies the kernels that consume the most GPU memory. `topk` returns the top N items at each evaluation time. Over multiple time points, more than 5 unique kernels may appear when different kernels enter the top 5 at different times.

```promql
topk(5, sum(backendai_container_utilization{container_metric_name="cuda_mem", value_type="current"}) by (kernel_id))
```

**Top 5 GPU Utilization by Kernel**

Monitor GPU utilization by kernel (top 5). It shows which kernels are actively using GPU compute. `topk` returns the top N items at each evaluation time. Over multiple time points, more than 5 unique kernels may appear when different kernels enter the top 5 at different times.

```promql
topk(5, sum(backendai_container_utilization{container_metric_name="cuda_util", value_type="current"}) by (kernel_id))
```

**Top 5 CPU Utilization Increase by Kernel**

Track CPU utilization increase rate by kernel (top 5). It shows CPU consumption trends over time. The query divides by 1000 to convert per-mille to percentage. `topk` returns the top N items at each evaluation time. Over multiple time points, more than 5 unique kernels may appear when different kernels enter the top 5 at different times.

```promql
topk(5, sum(increase(backendai_container_utilization{container_metric_name="cpu_util", value_type="current"}[5m])) by (kernel_id)) / 1000
```

**Network RX Traffic by Kernel**

Monitor network RX (receive) traffic by kernel. It tracks inbound network bandwidth usage per container.

```promql
sum(increase(backendai_container_utilization{container_metric_name="net_rx", value_type="current"}[5m])) by (kernel_id)
```

**Network TX Traffic by Kernel**

Monitor network TX (transmit) traffic by kernel. It tracks outbound network bandwidth usage per container.

```promql
sum(increase(backendai_container_utilization{container_metric_name="net_tx", value_type="current"}[5m])) by (kernel_id)
```

#### Device Utilization (Agent-level)

**GPU Memory Usage by Agent**

Monitor GPU memory usage at the agent level. It shows total GPU memory consumption on each agent node.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_mem", value_type="current"}) by (agent_id)
```

**GPU Memory Capacity by Agent**

Monitor GPU memory capacity. It shows the maximum available GPU memory on each agent.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_mem", value_type="capacity"}) by (agent_id)
```

**GPU Utilization Percentage by Agent**

Monitor GPU utilization percentage at the agent level. It shows overall GPU usage across all kernels on the agent.

```promql
sum(backendai_device_utilization{device_metric_name="cuda_util", value_type="current"}) by (agent_id)
```

**CPU Utilization Increase by Agent**

Track CPU utilization increase rate at the agent level. It shows agent-wide CPU consumption trends.

```promql
sum(increase(backendai_device_utilization{device_metric_name="cpu_util", value_type="current"}[5m])) by (agent_id) / 1000
```

**Network RX Traffic by Agent**

Monitor network RX (receive) traffic at the agent level. It tracks total inbound network bandwidth usage on each agent node.

```promql
sum(increase(backendai_device_utilization{device_metric_name="net_rx", value_type="current"}[5m])) by (agent_id)
```

**Network TX Traffic by Agent**

Monitor network TX (transmit) traffic at the agent level. It tracks total outbound network bandwidth usage on each agent node.

```promql
sum(increase(backendai_device_utilization{device_metric_name="net_tx", value_type="current"}[5m])) by (agent_id)
```

#### Container Lifecycle Synchronization

**Container Sync Trigger Frequency**

Monitor container sync trigger frequency. It shows how often the agent synchronizes container state with the manager.

```promql
sum(rate(backendai_sync_container_lifecycle_trigger_count_total[5m])) by (agent_id)
```

**Container Sync Success Rate**

Track container sync success rate. It confirms that containers are synchronized correctly.

```promql
sum(rate(backendai_sync_container_lifecycle_success_count_total[5m])) by (agent_id)
```

**Container Sync Failure Rate**

Monitor container sync failures. It identifies issues with container state synchronization.

```promql
sum(rate(backendai_sync_container_lifecycle_failure_count_total[5m])) by (agent_id, exception)
```

#### Statistics Collection

**Statistics Collection Trigger Rate**

Monitor statistics collection trigger rate by scope. It shows how often statistics are collected at different levels.

```promql
sum(rate(backendai_stat_task_trigger_count_total[5m])) by (agent_id, stat_scope)
```

**Statistics Collection Success Rate**

Track statistics collection success rate. It confirms that statistics collection works correctly.

```promql
sum(rate(backendai_stat_task_success_count_total[5m])) by (agent_id, stat_scope)
```

**Statistics Collection Failure Rate**

Monitor statistics collection failures. It identifies issues with resource monitoring.

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

## Related documents

- [Manager component](../manager/README.md) - Session orchestration
- [Storage proxy component](../storage/README.md) - vfolder management
- [Overall architecture](../README.md) - System-wide architecture
