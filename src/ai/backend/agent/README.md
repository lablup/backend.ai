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

## Architecture

```
┌────────────────────────────────────────┐
│         Agent Server (agent.py)        │
├────────────────────────────────────────┤
│    Container Backend (docker/)         │  ← Docker
├────────────────────────────────────────┤
│  Resource Monitor (watcher/ stats.py)  │  ← CPU, GPU, Memory
├────────────────────────────────────────┤
│   Storage Manager (scratch.py fs.py)   │  ← Local and mounted storage
├────────────────────────────────────────┤
│      Plugin System (plugin/)           │  ← Accelerator plugins
└────────────────────────────────────────┘
```

## Directory Structure

```
agent/
├── docker/              # Docker container backend
│   ├── agent.py        # Docker-specific agent implementation
│   └── resources.py    # Docker resource management
├── watcher/             # Resource monitoring
│   ├── cpu.py          # CPU monitoring
│   ├── mem.py          # Memory monitoring
│   └── gpu.py          # GPU monitoring
├── plugin/              # Accelerator plugins
│   ├── cuda.py         # NVIDIA CUDA support
│   ├── rocm.py         # AMD ROCm support
│   └── tpu.py          # Google TPU support
├── observer/            # Metrics observers
│   └── stat.py         # Statistics collection
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
- **Location**: `/tmp/backend.ai/scratches/{kernel_id}`
- **Quota**: Configurable size limit per kernel
- **Cleanup**: Automatically removed after kernel termination
- **Performance**: Local SSD for fast I/O

### Virtual Folder Mounting
VFolders are mounted to containers at runtime:
- **Mount Point**: `/home/work/{vfolder_name}`
- **Permissions**: RO, RW, or RW-DELETE
- **Backend**: Storage Proxy manages actual storage
- **Protocol**: NFS, SMB, or direct mount

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

The Agent uses plugins for accelerator support:

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
- **Protocol**: HTTP or NFS/SMB
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
  - Retrieve global configuration (container registry, storage volumes, etc.)
  - Auto-discover Manager address

### Optional Infrastructure (Observability)

Optional infrastructure for Agent monitoring.

#### Prometheus (Metrics Collection)
- **Purpose**:
  - Monitor agent resource utilization
  - Collect kernel (container) metrics
  - Track heartbeat and health status
- **Exposed Endpoint**: `http://localhost:6009/metrics`
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
- **Protocol**: NFS, SMB, direct mount
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

- `backendai_rpc_requests_total`: Total RPC requests
  - Labels: method
  - Tracks processing frequency by Manager command type

- `backendai_rpc_failure_requests_total`: Failed RPC requests
  - Labels: method, exception
  - Analyzes RPC command processing failure causes

- `backendai_rpc_request_duration_seconds`: RPC request processing time (seconds)
  - Labels: method
  - Measures performance of RPC commands like kernel creation/deletion

#### Resource Utilization Metrics
Metrics related to container and hardware resource usage.

- `backendai_container_utilization`: Container resource utilization
  - Labels: container_metric_name, agent_id, kernel_id, session_id, user_id, project_id, value_type
  - Tracks resource usage per kernel (CPU, memory, GPU, etc.)

- `backendai_device_utilization`: Physical device utilization
  - Labels: device_metric_name, agent_id, device_id, value_type
  - Tracks hardware device usage (GPU, NPU, etc.) on agent node

#### Container Lifecycle Synchronization Metrics
Metrics related to container state synchronization operations.

- `backendai_sync_container_lifecycle_trigger_count`: Synchronization trigger count
  - Labels: agent_id
  - Frequency of container state synchronization between Manager and Agent

- `backendai_sync_container_lifecycle_success_count`: Synchronization success count
  - Labels: agent_id
  - Number of successfully synchronized kernels

- `backendai_sync_container_lifecycle_failure_count`: Synchronization failure count
  - Labels: agent_id, exception
  - Tracks synchronization failure causes

#### Statistics Collection Task Metrics
Metrics related to node, container, and process level statistics collection.

- `backendai_stat_task_trigger_count`: Statistics collection trigger count
  - Labels: agent_id, stat_scope
  - Collection frequency by Node/Container/Process level

- `backendai_stat_task_success_count`: Statistics collection success count
  - Labels: agent_id, stat_scope
  - Tracks statistics collection success rate

- `backendai_stat_task_failure_count`: Statistics collection failure count
  - Labels: agent_id, stat_scope, exception
  - Analyzes statistics collection failure causes

### Logs
Agent logs include:
- Kernel creation and termination events
- Resource allocation and release
- Error situations and recovery operations
- RPC request/response tracking

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Manager Component](../manager/README.ko.md) - Session orchestration
- [Storage Proxy Component](../storage/README.ko.md) - Virtual folder management
- [Overall Architecture](../README.ko.md) - System-wide architecture
