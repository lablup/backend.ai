# Backend.AI Storage Proxy

## Purpose

The Storage Proxy provides a unified abstraction layer for various storage backends, manages virtual folders (vfolders), and handles file operations. It supports enterprise storage systems and allows seamless switching of storage backends without impacting users.

## Key Responsibilities

### 1. Virtual Folder Management
- Create, delete, and list virtual folders
- Manage vfolder permissions (owner, group, read-only)
- Track vfolder quotas and usage
- Handle vfolder cloning and snapshots

### 2. File Operations
- Upload and download files to/from vfolders
- List directory contents recursively
- Create, rename, move, and delete files/folders
- Stream large files efficiently

### 3. Storage Backend Abstraction
- Abstract multiple storage systems (NFS, CephFS, NetApp, etc.)
- Provide uniform API regardless of backend
- Handle backend-specific optimizations
- Support multi-backend environments

### 4. Access Control
- Validate user permissions for vfolder access
- Enforce read-only vs read-write access
- Support shared vfolders between users/groups
- Integrate with Manager's permission system

### 5. Performance Optimization
- Cache vfolder metadata
- Stream file transfers for efficiency
- Support parallel uploads/downloads
- Optimize large file operations

## Entry Points

Storage Proxy has 4 entry points to receive and process external requests.

### 1. REST API (Client)

**Framework**: aiohttp (async HTTP server)

**Port**: 6021 (default)

**Location**: `src/ai/backend/storage/api/client.py`

**Purpose**: External API used by Client SDK/CLI/Web UI

**Key Features**:
- File upload/download and VFolder management
- API Key-based authentication
- HTTP/HTTPS communication

### 2. REST API (Manager)

**Framework**: aiohttp (async HTTP server)

**Port**: 6022 (default, separate from Client API)

**Location**: `src/ai/backend/storage/api/manager.py`

**Purpose**: Internal API used by Manager and Agent

**Key Features**:
- Manager-only API (internal network access only)
- Provides VFolder mount information (used by Agent)
- Volume and Quota management

### 3. Event Dispatcher

**Framework**: Backend.AI Event Dispatcher (Redis Streams-based)

**Location**: `src/ai/backend/common/events/`

**Key Features**:
- VFolder lifecycle event publishing and consumption
- Broadcast and Anycast event type support

**Related Documentation**: [Event Dispatcher System](../common/events/README.md)

### 4. Background Task Handler

**Framework**: Backend.AI Background Task Handler (Valkey-based)

**Location**: `src/ai/backend/common/bgtask/`

**Related Documentation**: [Background Task Handler System](../common/bgtask/README.md)

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

**Supported Storage Backends**: See `volumes/` directory for available backend implementations.

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

### Virtual Folders (VFolders)
Virtual folders are logical storage units:
- **ID**: Unique identifier (UUID)
- **Name**: Human-readable name
- **Type**: User-owned or group-shared
- **Backend**: Storage backend (cephfs, netapp, etc.)
- **Host**: Physical storage host or path
- **Quota**: Storage limit (bytes)
- **Permissions**: Owner, group members with RO/RW access

### Storage Backends
Each backend implements a common interface:
- `create_vfolder()`: Create new vfolder
- `delete_vfolder()`: Delete existing vfolder
- `upload_file()`: Upload file to vfolder
- `download_file()`: Download file from vfolder
- `list_files()`: List files in vfolder
- `get_quota()`: Query vfolder usage and quota
- `set_quota()`: Update vfolder quota

**Supported backends**: See `volumes/` directory for available backend implementations.

### VFolder Types

#### User VFolder
- Owned by single user
- Private by default
- Can be shared with specific users
- Counted toward user quota

#### Group VFolder
- Shared among group members
- Managed by group administrators
- Counted toward group quota
- Supports fine-grained permissions

### Permissions
VFolder access modes:
- **Read-Only (RO)**: Can read files but not modify
- **Read-Write (RW)**: Can read and write files
- **Read-Write-Delete (RWD)**: Full access including deletion

Permissions are checked at:
- Vfolder mount time by Agent
- File operation time by Storage Proxy
- Through Manager's permission layer

### Quotas
Storage quotas are enforced:
- **Per-vfolder quota**: Maximum size for each vfolder
- **Per-user quota**: Total storage across all user vfolders
- **Per-group quota**: Total storage across all group vfolders

Quota tracking:
- Real-time usage monitoring
- Periodic scans for accuracy
- Alerts when approaching limits

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

## VFolder Mounting

When a session is created:
1. Manager requests vfolder mount from Storage Proxy
2. Storage Proxy returns mount credentials/path
3. Agent mounts vfolder to container
4. Container accesses vfolder at `/home/work/{vfolder_name}`

Mount methods:
- **NFS**: Mount NFS export directly
- **FUSE**: Use FUSE filesystem driver
- **Direct**: Direct filesystem access (local storage)

## Background Tasks

### Storage Scanning
- Periodically scan vfolders to update usage statistics
- Detect orphaned vfolders
- Validate quota consistency

### Cleanup
- Remove deleted vfolders from storage
- Clean up expired temporary vfolders
- Remove old snapshots

## Performance Optimization

### Caching
- Cache vfolder metadata in Redis
- Cache user permissions
- Invalidate cache on updates

### Connection Pooling
- Maintain connection pools to storage backends
- Reuse connections across multiple requests
- Handle connection failures gracefully

### Async I/O
- Use async I/O for file operations
- Stream large files asynchronously
- Handle multiple concurrent requests

## Communication Protocols

### Client/Manager → Storage Proxy
- **Protocol**: HTTP/HTTPS or gRPC
- **Port**: 6021 (default)
- **Authentication**: API key or JWT token
- **Operations**: All vfolder and file operations

### Storage Proxy → Backend Storage
- **NFS**: NFS protocol (port 2049)
- **CephFS**: CephFS native protocol
- **REST API**: HTTPS for storage management APIs
- **SMB**: SMB protocol (port 445)

## Configuration

See `configs/storage-proxy/halfstack.toml` for configuration file examples.

### Key Configuration Items

**Basic Settings**:
- Listen address and port
- Backend volume definitions
- Cache settings (if using Redis)

**Backend-specific Settings**:
- CephFS: Monitor hosts, paths
- NetApp: Management API, SVM information
- XFS: Local paths

## Infrastructure Dependencies

### Required Infrastructure

Storage Proxy connects directly to storage backends and has no separate required infrastructure.

#### Storage Backend
- **Purpose**: Actual file storage and management
- **Supported Backends**:
  - CephFS: Distributed filesystem
  - NetApp ONTAP: Enterprise storage
  - Pure Storage FlashBlade: All-flash storage
  - Dell EMC Isilon/PowerScale
  - WekaFS, VAST, DDN
  - XFS: Local filesystem
  - NFS: Generic network filesystem
- **Connection Methods**:
  - NFS mount
  - Native protocol (CephFS)
  - REST API (management operations)

#### etcd (Global Configuration)
- **Purpose**:
  - Retrieve global configuration (storage volume settings, backend information, etc.)
  - Auto-discover Manager address
- **Halfstack Port**: 8121 (host) → 2379 (container)

### Optional Infrastructure

#### Manager Connection
- **Purpose**: User authentication, vfolder metadata synchronization
- **Protocol**: HTTP/gRPC
- **Operations**:
  - Validate vfolder permissions
  - Query user information
  - Synchronize quota information

#### Redis (Caching)
- **Purpose**:
  - Cache vfolder metadata
  - Cache user permissions
  - Store temporary upload state
  - Manage background tasks
- **Halfstack Port**: 8111 (shared with Manager)
- **Key Patterns**:
  - `vfolder:{vfolder_id}:*` - VFolder metadata
  - `user:{user_id}:perms` - User permissions
  - `upload:{upload_id}` - Upload sessions
- **Note**: Redis is optional; works without it but recommended for performance

#### Prometheus (Metrics Collection)
- **Purpose**:
  - VFolder operation metrics
  - File upload/download performance
  - Storage backend performance
- **Internal Port**: 16023 (separate from client API port 6021 and manager API port 6022)
- **Exposed Endpoint**: `http://localhost:16023/metrics`
- **Key Metrics**:
  - `backendai_api_request_count` - Total API requests
  - `backendai_api_request_duration_sec` - Request processing time

#### Loki (Log Aggregation)
- **Purpose**:
  - VFolder operation logs
  - File upload/download tracking
  - Backend error logs
- **Log Labels**:
  - `vfolder_id` - VFolder identifier
  - `backend` - Storage backend type
  - `operation` - Operation type (upload, download, etc.)

### Storage Backend Requirements

#### CephFS
- **Client Requirements**:
  - libcephfs or ceph-fuse
  - Access to Ceph Monitors
- **Network**: 10GbE or higher recommended

#### NetApp ONTAP
- **API Access**: HTTPS REST API
- **Protocol**: NFS or SMB
- **Permissions**: SVM administrator permissions

#### Local XFS
- **Mount**: Direct filesystem access
- **Quota**: XFS project quota support
- **Recommended**: Development/testing environments

### Halfstack Configuration

**Recommended**: Use the `./scripts/install-dev.sh` script for development environment setup.

#### Starting Development Environment
```bash
# Setup development environment via script (recommended)
./scripts/install-dev.sh

# Start Storage Proxy
./backend.ai storage start-server
```

#### Development Environment with MinIO
Halfstack includes S3-compatible MinIO:
- MinIO console: http://localhost:9001
- API endpoint: http://localhost:9000
- Default credentials: minioadmin / minioadmin

## Metrics and Monitoring

### Prometheus Metrics

The Storage Proxy component exposes Prometheus metrics at the `/metrics` endpoint for monitoring vfolder operations and file transfer performance.

#### API Metrics

Metrics related to vfolder and file operation API request processing.

**`backendai_api_request_count`** (Counter)
- **Description**: Total number of API requests received by the Storage Proxy
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
  - `endpoint`: Request endpoint path (e.g., "/vfolder/upload", "/vfolder/download")
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

### Prometheus Query Examples

The following examples demonstrate common Prometheus queries for Storage Proxy metrics. Note that Counter metrics use the `_total` suffix and Histogram metrics use `_bucket`, `_sum`, `_count` suffixes in actual queries.

**Important Notes:**
- When using `increase()` or `rate()` functions, the time range must be at least 2-4x longer than your Prometheus scrape interval to get reliable data. If the time range is too short, metrics may not appear or show incomplete data.
- Default Prometheus scrape interval is typically 15s-30s
- **Time range selection trade-offs**:
  - Shorter ranges (e.g., `[1m]`): Detect changes faster with more granular data, but more sensitive to noise and short-term fluctuations
  - Longer ranges (e.g., `[5m]`): Smoother graphs with reduced noise, better for identifying trends, but slower to detect sudden changes
  - For real-time alerting: Use shorter ranges like `[1m]` or `[2m]`
  - For dashboards and trend analysis: Use longer ranges like `[5m]` or `[10m]`
- File upload/download operations may have longer durations, consider using larger time buckets for analysis

#### VFolder Operations

**VFolder Operation Rate by Endpoint**

Monitor vfolder operation rate by endpoint. This shows how frequently users create, delete, and access vfolders. Use this to understand storage usage patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m])) by (method, endpoint, status_code)
```

**Failed VFolder Operations**

Track failed vfolder operations. This helps identify permission issues, quota violations, and backend errors.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"[45].."}[5m])) by (endpoint, status_code, error_detail)
```

**VFolder Creation Rate**

Monitor vfolder creation rate. This shows how many new vfolders are being created.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/create"}[5m]))
```

#### File Upload/Download Performance

**P95 File Upload Duration**

Calculate P95 file upload duration. This shows upload performance experienced by users. Use this to identify slow uploads and storage bottlenecks.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/upload"}[5m])) by (le)
)
```

**P95 File Download Duration**

Calculate P95 file download duration. This shows download performance experienced by users.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/download"}[5m])) by (le)
)
```

**File Upload Rate**

Monitor file upload rate. This shows how frequently users are uploading files.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
```

**File Download Rate**

Monitor file download rate. This shows how frequently users are downloading files.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/download"}[5m]))
```

**Average Upload Duration**

Calculate average upload duration. This provides a simple overview of file transfer performance.

```promql
sum(rate(backendai_api_request_duration_sec_sum{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
/
sum(rate(backendai_api_request_duration_sec_count{service_group="$service_groups", endpoint="/vfolder/upload"}[5m]))
```

#### Storage Backend Performance

**Storage Operation Errors**

Monitor storage operation errors. This identifies issues with backend storage systems. High error rates may indicate storage hardware problems or network issues.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="500"}[5m])) by (endpoint, error_detail)
```

**Slow Storage Operations (> 10s)**

Track slow storage operations (> 10 seconds). This identifies operations that exceed acceptable performance thresholds.

```promql
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="10"}[5m])) by (endpoint)
-
sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", le="1"}[5m])) by (endpoint)
```

**Storage Timeout Errors**

Monitor timeout errors. This helps identify when storage operations are taking too long.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="504"}[5m])) by (endpoint)
```

#### Directory Operations

**Directory Listing Rate**

Monitor directory listing operations. This shows how frequently users are browsing vfolder contents.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint="/vfolder/list"}[5m]))
```

**P95 Directory Operation Duration**

Track directory operation duration. This shows how long it takes to list directory contents.

```promql
histogram_quantile(0.95,
  sum(rate(backendai_api_request_duration_sec_bucket{service_group="$service_groups", endpoint="/vfolder/list"}[5m])) by (le)
)
```

#### Quota Management

**Quota Check Operations**

Monitor quota check operations. This shows how frequently quota information is being queried.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", endpoint=~".*quota.*"}[5m])) by (endpoint)
```

**Quota Violations**

Track quota violations (403 errors). This identifies when users hit storage limits.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="403", error_detail=~".*quota.*"}[5m]))
```

#### Permission Issues

**Permission Denied Errors**

Monitor permission denied errors. This identifies unauthorized access attempts or misconfigured permissions.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="403"}[5m])) by (endpoint)
```

**Authentication Failures**

Track authentication failures. This shows failed authentication attempts to storage proxy.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code="401"}[5m]))
```

#### Overall Storage Health

**Storage Operation Success Rate**

Calculate overall storage operation success rate. This provides a high-level view of storage system health.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups", status_code=~"2.."}[5m]))
/
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m]))
```

**Overall Request Rate Trends**

Monitor request rate trends. This shows overall storage workload patterns.

```promql
sum(rate(backendai_api_request_count_total{service_group="$service_groups"}[5m]))
```

### Logs
- Vfolder creation/deletion events
- File operation tracking (upload, download, delete)
- Quota violations and limit warnings
- Backend errors and connection issues
- Permission denied events

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Manager Component](../manager/README.md) - Session orchestration
- [Agent Component](../agent/README.md) - VFolder mounting
- [Overall Architecture](../README.md) - System-wide architecture
