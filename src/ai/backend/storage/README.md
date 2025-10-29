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
│  ├── CephFS                             │
│  ├── NetApp                             │
│  ├── PureStorage                        │
│  ├── Dell EMC                           │
│  └── ...                                │
└─────────────────────────────────────────┘
```

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
│   ├── cephfs/         # CephFS support
│   ├── netapp/         # NetApp support
│   ├── purestorage/    # Pure Storage support
│   ├── dellemc/        # Dell EMC support
│   ├── weka/           # WekaFS support
│   └── ...
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

Supported backends:
- **CephFS**: Ceph filesystem
- **NetApp**: NetApp ONTAP storage
- **Pure Storage**: Pure Storage FlashBlade
- **Dell EMC**: Dell EMC Isilon/PowerScale
- **WekaFS**: Weka filesystem
- **VAST**: VAST Data storage
- **DDN**: DataDirect Networks storage
- **XFS**: Local XFS filesystem
- **NFS**: Generic NFS mount

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

#### API Metrics
Metrics related to vfolder and file operation API request processing.

- `backendai_api_request_count`: Total API requests
  - Labels: method, endpoint, domain, operation, error_detail, status_code
  - Tracks vfolder operations and file upload/download requests

- `backendai_api_request_duration_sec`: API request processing time (seconds)
  - Labels: method, endpoint, domain, operation, error_detail, status_code
  - Measures file transfer and storage operation performance

### Logs
- Vfolder creation/deletion events
- File operation tracking
- Quota violations
- Backend errors

## Development

See [README.md](./README.md) for development setup instructions.

## Related Documentation

- [Manager Component](../manager/README.md) - Session orchestration
- [Agent Component](../agent/README.md) - VFolder mounting
- [Overall Architecture](../README.md) - System-wide architecture
