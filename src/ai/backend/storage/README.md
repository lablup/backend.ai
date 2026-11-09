# Backend.AI Storage Proxy

## Purpose

The storage proxy provides a unified abstraction layer for various storage backends, manages vfolders and handles file operations. It supports enterprise storage systems and allows seamless switching of storage backends without impacting users.

## Key Responsibilities

### 1. Vfolder management
- Create, delete and list vfolders
- Manage vfolder permissions (owner, project, read-only)
- Track vfolder quotas and usage
- Handle vfolder cloning and snapshots

### 2. File Operations
- Upload files to vfolders and download files from vfolders
- List directory contents recursively
- Create, rename, move and delete files and folders
- Stream large files efficiently

### 3. Storage Backend Abstraction
- Abstract multiple storage systems (NFS, CephFS, NetApp, etc.)
- Provide a uniform API regardless of the backend
- Handle backend-specific optimizations
- Support multi-backend environments

### 4. Access Control
- Validate user permissions for vfolder access
- Enforce read-only or read-write access
- Support shared vfolders between users and projects
- Integrate with the manager permission system

### 5. Performance Optimization
- Cache vfolder metadata
- Stream file transfers for efficiency
- Support parallel uploads and downloads
- Optimize large file operations

## Entry Points

The storage proxy has 4 entry points that receive and process external requests.

### 1. REST API (client)

**Framework**: aiohttp (async HTTP server)

**Port**: 6021 (default)

**Location**: `src/ai/backend/storage/api/client.py`

**Purpose**: External API used by the client SDK/CLI/WebUI

**Key Features**:
- File upload, file download and vfolder management
- API key-based authentication
- HTTP/HTTPS communication

### 2. REST API (manager)

**Framework**: aiohttp (async HTTP server)

**Port**: 6022 (default, separate from the storage proxy client API)

**Location**: `src/ai/backend/storage/api/manager.py`

**Purpose**: Internal API used by the manager and the Agent

**Key Features**:
- manager-only API (internal network access only)
- Provides vfolder mount information (used by the Agent)
- Volume and quota management

### 3. Event Dispatcher

**Framework**: Backend.AI Event Dispatcher (Valkey Streams-based)

**Location**: `src/ai/backend/common/events/`

**Key Features**:
- Vfolder lifecycle event publishing and consumption
- Broadcast and Anycast event type support

**Related documents**: [Event Dispatcher System](../common/events/README.md)

### 4. Background Task Handler

**Framework**: Backend.AI Background Task Handler (Valkey-based)

**Location**: `src/ai/backend/common/bgtask/`

**Related documents**: [Background Task Handler System](../common/bgtask/README.md)

## Architecture

```
┌─────────────────────────────────────────┐
│         API Layer (api/)                │  ← REST API
├─────────────────────────────────────────┤
│      Services Layer (services/)         │  ← Business logic
├─────────────────────────────────────────┤
│       VFS Layer (vfs/)                  │  ← Virtual filesystem
├─────────────────────────────────────────┤
│  Storage Backends (storages/)           │  ← Backend implementations
│  └── ...                                │
└─────────────────────────────────────────┘
```

**Supported storage backends**: See the `volumes/` directory for the available backend implementations.

## Directory Structure

```
storage/
├── api/                 # REST API endpoints
│   ├── client.py       # Client-facing API
│   └── manager.py      # Manager-facing API
├── services/           # Business logic
│   ├── vfolder.py      # VFolder management
│   └── quota.py        # Quota management
├── vfs/                # Virtual filesystem abstraction
│   ├── base.py         # VFS base classes
│   └── local.py        # Local filesystem implementation
├── storages/           # Backend-specific implementations
│   └── ...             # See volumes/ directory
├── volumes/            # Volume management
│   └── quota.py        # Quota tracking
├── bgtask/             # Background tasks
│   ├── scan.py         # Storage scanning
│   └── cleanup.py      # Cleanup tasks
├── cli/                # CLI commands
├── config/             # Configuration
├── server.py           # API server entry point
└── plugin.py           # Plugin system
```

## Core Concepts

### Vfolders
A vfolder is a logical storage unit:
- **ID**: Unique identifier (UUID)
- **Name**: Human-readable name
- **Type**: User-owned or project-shared
- **Backend**: Storage backend (cephfs, netapp, etc.)
- **Host**: Physical storage host or path
- **Quota**: Storage limit (bytes)
- **Permissions**: Owner, project members with RO or RW access

### Storage backends
Each backend implements a common interface:
- `create_vfolder()`: Create new vfolder
- `delete_vfolder()`: Delete existing vfolder
- `upload_file()`: Upload file to vfolder
- `download_file()`: Download file from vfolder
- `list_files()`: List files in vfolder
- `get_quota()`: Query vfolder usage and quota
- `set_quota()`: Update vfolder quota

**Supported backends**: See the `volumes/` directory for the available backend implementations.

### Vfolder types

#### User vfolder
- Owned by a single user
- Private by default
- Can be shared with specific users
- Counted toward the user quota

#### Project vfolder
- Shared among project members
- Managed by project admins
- Counted toward the project quota
- Supports fine-grained permissions

### Permissions
Vfolder access modes:
- **Read-Only (RO)**: Can read files but not modify them
- **Read-Write (RW)**: Can read and write files
- **Read-Write-Delete (RWD)**: Full access including deletion

Permissions are checked at:
- Vfolder mount time by the Agent
- File operation time by the storage proxy
- The manager permission layer

### Quotas
Storage quotas are enforced:
- **Per-vfolder quota**: Maximum size for each vfolder
- **Per-user quota**: Total storage across all user vfolders
- **Per-project quota**: Total storage across all project vfolders

Quota tracking:
- Real-time usage monitoring
- Periodic scans for accuracy
- Alerts when usage approaches the limits

## Storage Backend Details

### CephFS
- **Protocol**: CephFS native or NFS export
- **Features**: Distributed, scalable, POSIX-compliant
- **Quota**: Native CephFS quota support
- **Mount**: libcephfs or kernel mount

### NetApp ONTAP
- **Protocol**: NFS or SMB
- **Features**: Enterprise-grade, snapshots, replication
- **Quota**: Qtree or volume quotas
- **API**: REST API for management

### Pure Storage FlashBlade
- **Protocol**: NFS
- **Features**: All-flash, high-performance
- **Quota**: Directory quotas
- **API**: REST API for management

### Local Filesystem (XFS)
- **Protocol**: Direct filesystem access
- **Features**: Simple, no network overhead
- **Quota**: XFS project quotas
- **Use case**: Single-node or testing

## File Operations

### Upload Flow
```
1. Client initiates upload via API
   ↓
2. Storage Proxy validates permissions
   ↓
3. Storage Proxy checks quota
   ↓
4. Backend writes file to storage
   ↓
5. Storage Proxy updates metadata
   ↓
6. Return success to client
```

### Download Flow
```
1. Client requests download via API
   ↓
2. Storage Proxy validates permissions
   ↓
3. Backend streams file from storage
   ↓
4. Storage Proxy proxies stream to client
   ↓
5. Client receives file
```

### Large File Handling
- **Chunked Transfer**: Split large files into chunks
- **Resumable Upload**: Resume interrupted uploads
- **Streaming**: Stream files without full buffering
- **Multipart**: Parallel chunk uploads

## Vfolder mounting

When a session is created:
1. The manager requests a vfolder mount from the storage proxy
2. The storage proxy returns the mount credentials or path
3. The Agent mounts the vfolder to the container
4. The container accesses the vfolder at `/home/work/{vfolder_name}`

Mount methods:
- **NFS**: Mount NFS export directly
- **FUSE**: Use FUSE filesystem driver
- **Direct**: Direct filesystem access (local storage)

## Background Tasks

### Storage scanning
- Periodically scan vfolders to update usage statistics
- Detect orphaned vfolders
- Validate quota consistency

### Cleanup
- Remove deleted vfolders from storage
- Clean up expired temporary vfolders
- Remove old snapshots

## Performance Optimization

### Caching
- Cache vfolder metadata in Valkey
- Cache user permissions
- Invalidate cache on updates

### Connection pooling
- Maintain connection pools to storage backends
- Reuse connections across multiple requests
- Handle connection failures gracefully

### Async I/O
- Use async I/O for file operations
- Stream large files asynchronously
- Handle multiple concurrent requests

## Communication Protocols

### Client and manager → storage proxy
- **Protocol**: HTTP/HTTPS or gRPC
- **Port**: 6021 (default)
- **Authentication**: API key or JWT token
- **Operations**: All vfolder and file operations

### Storage proxy → storage backend
- **NFS**: NFS protocol (port 2049)
- **CephFS**: CephFS native protocol
- **REST API**: HTTPS for storage management APIs
- **SMB**: SMB protocol (port 445)

## Configuration

See `configs/storage-proxy/halfstack.toml` for configuration file examples.

### Key configuration items

**Basic settings**:
- Listen address and port
- Backend volume definitions
- Cache settings (if using Valkey)

**Backend-specific settings**:
- CephFS: Monitor hosts, paths
- NetApp: Management API, SVM information
- XFS: Local paths

## Infrastructure Dependencies

### Required infrastructure

The storage proxy connects directly to storage backends and has no separate required infrastructure.

#### Storage backend
- **Purpose**: Actual file storage and management
- **Supported backends**:
  - CephFS: Distributed filesystem
  - NetApp ONTAP: Enterprise storage
  - Pure Storage FlashBlade: All-flash storage
  - Dell EMC Isilon/PowerScale
  - WekaFS, VAST, DDN
  - XFS: Local filesystem
  - NFS: Generic network filesystem
- **Connection methods**:
  - NFS mount
  - Native protocol (CephFS)
  - REST API (management operations)

#### etcd (global configuration)
- **Purpose**:
  - Retrieve global configuration (storage volume settings, backend information, etc.)
  - Auto-discover the manager address
- **Halfstack port**: 8121 (host) → 2379 (container)

### Optional infrastructure

#### Manager connection
- **Purpose**: User authentication, vfolder metadata synchronization
- **Protocol**: HTTP/gRPC
- **Operations**:
  - Validate vfolder permissions
  - Query user information
  - Synchronize quota information

#### Valkey (caching)
- **Purpose**:
  - Cache vfolder metadata
  - Cache user permissions
  - Store temporary upload state
  - Manage background tasks
- **Halfstack port**: 8111 (shared with the manager)
- **Key patterns**:
  - `vfolder:{vfolder_id}:*` - Vfolder metadata
  - `user:{user_id}:perms` - User permissions
  - `upload:{upload_id}` - Upload state
- **Note**: Valkey is optional; it works without it but is recommended for performance

#### Prometheus (metrics collection)
- **Purpose**:
  - Vfolder operation metrics
  - File upload/download performance
  - Storage backend performance
- **Internal port**: 16023 (separate from the storage proxy client API port 6021 and the storage proxy manager API port 6022)
- **Exposed endpoint**: `http://localhost:16023/metrics`
- **Key metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time

#### Loki (log aggregation)
- **Purpose**:
  - Vfolder operation logs
  - File upload/download tracking
  - Backend error logs
- **Log labels**:
  - `vfolder_id` - Vfolder identifier
  - `backend` - Storage backend type
  - `operation` - Operation type (upload, download, etc.)

### Storage backend requirements

#### CephFS
- **Client requirements**:
  - libcephfs or ceph-fuse
  - Access to Ceph Monitors
- **Network**: 10GbE or higher recommended

#### NetApp ONTAP
- **API access**: HTTPS REST API
- **Protocol**: NFS or SMB
- **Permissions**: SVM administrator permissions

#### Local XFS
- **Mount**: Direct filesystem access
- **Quota**: XFS project quota support
- **Recommended**: Development/testing environments

### Halfstack configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

#### Starting the development environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Storage Proxy
./backend.ai storage start-server
```

#### Development environment with MinIO
Halfstack includes S3-compatible MinIO:
- MinIO console: http://localhost:9001
- API endpoint: http://localhost:9000
- Default credentials: minioadmin / minioadmin

## Metrics and monitoring

### Prometheus metrics

The storage proxy exposes Prometheus metrics at the `/metrics` endpoint to monitor vfolder operations and file transfer performance.

#### API metrics

Metrics related to vfolder and file operation API request processing.

**`backendai_api_request_count`** (Counter)
- **Description**: Total number of API requests received by the storage proxy
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: Request endpoint path (for example, "/vfolder/upload", "/vfolder/download")
  - `domain`: Error domain (empty if successful)
  - `operation`: Error operation (empty if successful)
  - `error_detail`: Error details (empty if successful)
  - `status_code`: HTTP response status code (200, 400, 500, etc.)
- Tracks vfolder operations and file upload/download requests

**`backendai_api_request_duration_sec`** (Histogram)
- **Description**: API request processing time in seconds
- **Labels**: Same as `backendai_api_request_count`
- **Buckets**: [0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30, 60] seconds
- Measures file transfer and storage operation performance

### Prometheus query examples

The examples below show common Prometheus queries for storage proxy metrics. Counter metrics use the `_total` suffix and Histogram metrics use the `_bucket`, `_sum`, `_count` suffixes in actual queries.

**Important notes:**
- When using `increase()` or `rate()` functions, the time range must be at least 2-4x longer than your Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or show incomplete data.
- Default Prometheus scrape interval is typically 15s-30s
- **Time range selection trade-offs**:
  - Shorter ranges (for example, `[1m]`): Detect changes faster with more granular data, but more sensitive to noise and short-term fluctuations
  - Longer ranges (for example, `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges like `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges like `[5m]` or `[10m]`
- File upload and download operations may take longer. Consider larger time buckets for analysis

#### Vfolder operations

**Vfolder operation rate by endpoint**

Monitor vfolder operation rate by endpoint. This shows how frequently users create, delete and access vfolders. Use this to understand storage usage patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m])) by (method, endpoint, status_code)
```

**Failed vfolder operations**

Track failed vfolder operations. This helps identify permission issues, quota violations and backend errors.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"[45].."}[5m])) by (endpoint, status_code, error_detail)
```

**Vfolder creation rate**

Monitor vfolder creation rate. This shows how many new vfolders users create.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/create"}[5m]))
```

#### File upload and download performance

**P95 file upload duration**

Calculate P95 file upload duration. This shows upload performance experienced by users. Use this to identify slow uploads and storage bottlenecks.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/upload"}[5m])) by (le)
)
```

**P95 file download duration**

Calculate P95 file download duration. This shows download performance experienced by users.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/download"}[5m])) by (le)
)
```

**File upload rate**

Monitor file upload rate. This shows how frequently users upload files.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
```

**File download rate**

Monitor file download rate. This shows how frequently users download files.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/download"}[5m]))
```

**Average upload duration**

Calculate average upload duration. This provides a simple overview of file transfer performance.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
```

#### Storage backend performance

**Storage operation errors**

Monitor storage operation errors. This identifies issues with backend storage systems. High error rates may indicate storage hardware problems or network issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="500"}[5m])) by (endpoint, error_detail)
```

**Slow storage operations (> 10s)**

Track slow storage operations (> 10 seconds). This identifies operations that exceed acceptable performance thresholds.

```promql
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="10"}[5m])) by (endpoint)
-
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="1"}[5m])) by (endpoint)
```

**Storage timeout errors**

Monitor timeout errors. This helps identify when storage operations are taking too long.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="504"}[5m])) by (endpoint)
```

#### Directory operations

**Directory listing rate**

Monitor directory listing operations. This shows how frequently users browse vfolder contents.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/list"}[5m]))
```

**P95 directory operation duration**

Track directory operation duration. This shows how long it takes to list directory contents.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/list"}[5m])) by (le)
)
```

#### Quota management

**Quota check operations**

Monitor quota check operations. This shows how frequently quota information is queried.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~".*quota.*"}[5m])) by (endpoint)
```

**Quota violations**

Track quota violations (403 errors). This identifies when users hit storage limits.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="403", error_detail=~".*quota.*"}[5m]))
```

#### Permission issues

**Permission denied errors**

Monitor permission denied errors. This identifies unauthorized access attempts or misconfigured permissions.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="403"}[5m])) by (endpoint)
```

**Authentication failures**

Track authentication failures. This shows failed authentication attempts to the storage proxy.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="401"}[5m]))
```

#### Overall storage health

**Storage operation success rate**

Calculate overall storage operation success rate. This provides a high-level view of storage system health.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"2.."}[5m]))
/
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m]))
```

**Overall request rate trends**

Monitor request rate trends. This shows overall storage workload patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m]))
```

### Logs
- Vfolder creation and deletion events
- File operation tracking (upload, download, delete)
- Quota violations and limit warnings
- Backend errors and connection issues
- Permission denied events

## Development

See [README.md](./README.md) for development setup instructions.

## Related documents

- [Manager Component](../manager/README.md) - Session orchestration
- [Agent Component](../agent/README.md) - Vfolder mounting
- [Overall Architecture](../README.md) - System-wide architecture
