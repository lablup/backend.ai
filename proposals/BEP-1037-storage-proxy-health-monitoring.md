---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-01-22
Created-Version: 26.2.0
Target-Version:
Implemented-Version:
---

# Volume Host Availability Check

## Motivation

When users perform vfolder operations, the storage backend (volume host) hosting that vfolder may be unreachable. Currently, there is no way to check this in advance, so users only become aware of the issue when the operation fails.

**Problems:**
- Cannot immediately determine if vfolder operation failure is due to storage backend inaccessibility
- Administrators cannot query the status of a specific volume (storage backend) via API
- Users cannot check the availability of the storage their vfolder uses in advance

## Terminology

- **Storage Proxy**: An intermediary service between Manager and actual storage backends. It exposes HTTP APIs for Manager to perform storage operations.
- **Volume / Storage Backend**: The actual storage system (GPFS cluster, Ceph cluster, NetApp ONTAP, NFS server, local filesystem, etc.) that stores data.
- **Volume Host**: A combination of storage proxy and the backend it manages (e.g., `proxy1:volume1`).

## Architecture Overview

### Current Architecture

```
┌─────────┐                        ┌───────────────┐                        ┌──────────────────┐
│         │   GET /manager-api/*   │               │   Backend-specific     │                  │
│ Manager │ ────────────────────── │ Storage Proxy │ ────────────────────── │ Storage Backend  │
│         │                        │               │        Protocol        │                  │
└─────────┘                        └───────────────┘                        └──────────────────┘
                                          │                                         │
                                   Only checks if                            - GPFS API Server
                                   proxy is alive                            - Ceph Cluster
                                                                             - NetApp ONTAP API
                                                                             - Local Filesystem
```

**Problem**: Manager only knows if the storage proxy is responding. It cannot distinguish between:
- Storage proxy down
- Storage proxy up, but backend storage unavailable

### Proposed Architecture

```
┌─────────┐                        ┌───────────────┐                        ┌──────────────────┐
│         │   GET /manager-api/*   │               │   Backend-specific     │                  │
│ Manager │ ────────────────────── │ Storage Proxy │ ────────────────────── │ Storage Backend  │
│         │                        │               │        Protocol        │                  │
└─────────┘                        └───────────────┘                        └──────────────────┘
     │                                    │                                         │
     │                                    │                                         │
     │   ┌────────────────────────────────┴─────────────────────────────────────────┤
     │   │                                                                          │
     │   │  Health Check Flow                                                       │
     │   │  ══════════════════                                                      │
     │   │                                                                          │
     │   │  1. Manager periodically calls GET /manager-api/health                   │
     │   │                                                                          │
     │   │  2. Storage Proxy returns:                                               │
     │   │     - Proxy health (is the service responding?)                          │
     │   │     - Per-volume backend health (via get_hwinfo())                       │
     │   │                                                                          │
     │   │  3. Manager caches results in HealthProbe                                │
     │   │                                                                          │
     │   │  4. GraphQL API exposes health status to clients                         │
     │   │                                                                          │
     │   └──────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              Manager HealthProbe                                     │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Proxy Health:                                                                   │ │
│  │   proxy1  -> HEALTHY                                                            │ │
│  │   proxy2  -> UNHEALTHY (error: "Connection refused")                            │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Volume Health:                                                                  │ │
│  │   proxy1:volume1  -> healthy  (backend: gpfs, info: "8/8 nodes online")         │ │
│  │   proxy1:volume2  -> offline  (backend: cephfs, info: "cluster unreachable")    │ │
│  │   proxy2:volume1  -> (unknown, proxy unreachable)                               │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## Two-Layer Health Monitoring

Storage Proxy health and Volume Backend health are tracked **independently**:

### Layer 1: Storage Proxy Health

Checks if the proxy service itself is responding to HTTP requests.

| Status | Description |
|--------|-------------|
| HEALTHY | Proxy service is responding |
| UNHEALTHY | Proxy service is not reachable |

### Layer 2: Volume Backend Health

Checks if the actual storage backend is accessible (via `get_hwinfo()`).

| Status | Description |
|--------|-------------|
| healthy | Backend is fully operational |
| offline | Backend is not accessible |
| unavailable | Backend connectivity cannot be determined |

### Failure Scenarios

| Proxy Status | Volume Status | User Impact |
|--------------|---------------|-------------|
| HEALTHY | healthy | Normal operation |
| HEALTHY | offline | Vfolder operations on this volume fail |
| HEALTHY | unavailable | Vfolder operations may fail |
| UNHEALTHY | (unknown) | All vfolder operations on this proxy fail |

### Backend-Specific Health Checks

Each storage backend has its own health check mechanism:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Backend Health Check Methods                         │
├─────────────┬───────────────────────────────────────────────────────────────┤
│ Backend     │ Health Check Method                                           │
├─────────────┼───────────────────────────────────────────────────────────────┤
│ GPFS        │ Queries GPFS API for node health status                       │
│ WekaFS      │ Calls api_client.check_health()                               │
│ VAST        │ Queries cluster state via API                                 │
│ NetApp      │ REST API connectivity check                                   │
│ CephFS      │ Filesystem xattr read test                                    │
│ VFS/XFS     │ shutil.disk_usage() check                                     │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

All backends implement `AbstractVolume.get_hwinfo()` which returns:

```
HardwareMetadata {
    status: "healthy" | "offline" | "unavailable"
    status_info: string | null    # Human-readable description
    metadata: dict                # Backend-specific details
}
```

## Data Flow

### Health Check Sequence

```
┌─────────┐          ┌───────────────┐          ┌──────────────────┐
│ Manager │          │ Storage Proxy │          │ Storage Backend  │
└────┬────┘          └───────┬───────┘          └────────┬─────────┘
     │                       │                           │
     │  GET /health          │                           │
     │──────────────────────>│                           │
     │                       │                           │
     │                       │  get_hwinfo() [cached]    │
     │                       │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─>│
     │                       │                           │
     │                       │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                       │  HardwareMetadata         │
     │                       │                           │
     │  {                    │                           │
     │    "status": "healthy"│                           │
     │    "volumes": {       │                           │
     │      "vol1": {...},   │                           │
     │      "vol2": {...}    │                           │
     │    }                  │                           │
     │  }                    │                           │
     │<──────────────────────│                           │
     │                       │                           │
     │  Store in HealthProbe │                           │
     │                       │                           │
```

### GraphQL Query Flow

```
┌────────┐          ┌─────────┐          ┌─────────────┐
│ Client │          │ Manager │          │ HealthProbe │
└───┬────┘          └────┬────┘          └──────┬──────┘
    │                    │                      │
    │  query {           │                      │
    │    storageHealthList { ... }              │
    │  }                 │                      │
    │───────────────────>│                      │
    │                    │                      │
    │                    │  get_service_health  │
    │                    │  (STORAGE)           │
    │                    │─────────────────────>│
    │                    │                      │
    │                    │<─────────────────────│
    │                    │  ServiceHealth       │
    │                    │                      │
    │  [                 │                      │
    │    {               │                      │
    │      proxyName,    │                      │
    │      volumes: [...│                      │
    │    }               │                      │
    │  ]                 │                      │
    │<───────────────────│                      │
    │                    │                      │
```

## API Design

### Extended Health Endpoint Response

```json
{
    "status": "healthy",
    "version": "26.2.0",
    "volumes": {
        "volume1": {
            "status": "healthy",
            "status_info": "GPFS cluster healthy, 8/8 nodes online",
            "backend": "gpfs",
            "last_checked_at": "2026-01-22T10:00:00Z"
        },
        "volume2": {
            "status": "offline",
            "status_info": "Ceph cluster unreachable",
            "backend": "cephfs",
            "last_checked_at": "2026-01-22T10:00:00Z"
        }
    }
}
```

### GraphQL Queries

```graphql
# Get all storage proxy health status
query {
    storageProxyHealthList {
        proxyName
        status          # HEALTHY | UNHEALTHY
        isHealthy
        lastCheckedAt
        errorMessage
    }
}

# Get all volume backend health status
query {
    volumeHealthList {
        proxyName
        volumeId
        backendType     # "gpfs", "cephfs", "vfs", etc.
        status          # HEALTHY | OFFLINE | UNAVAILABLE | UNKNOWN
        statusInfo
        isHealthy
        lastCheckedAt
    }
}

# Get specific volume health
query {
    volumeHealth(host: "proxy1:volume1") {
        proxyName
        volumeId
        backendType
        status
        statusInfo
        isHealthy
        lastCheckedAt
    }
}

# Check vfolder's storage health
query {
    vfolderNode(id: "...") {
        name
        host
        storageHealth {
            backendType
            status
            statusInfo
            isHealthy
        }
    }
}
```

## Configuration

Health check intervals are configurable per volume to accommodate different backend characteristics:

```toml
# storage-proxy.toml
[volume.local]
backend = "vfs"
health_check_interval = "30s"   # Fast local checks

[volume.gpfs-cluster]
backend = "gpfs"
health_check_interval = "5m"    # Longer interval for API-heavy checks
```

## Migration / Compatibility

- **Backward compatible**: All changes are additive
- Old clients calling `/manager-api/health` receive the same top-level `status` field
- `storageHealth` GraphQL field is nullable

## Implementation Plan

| Phase | Work |
|-------|------|
| 1 | Extend storage proxy health endpoint with volume health |
| 2 | Add health check methods to `StorageProxyManagerFacingClient` |
| 3 | Implement and register `StorageHealthChecker` |
| 4 | Add GraphQL `storageHealthList` and `volumeHealth` queries |
| 5 | Add `VirtualFolderNode.storageHealth` field |
| 6 | Write tests |

See [Implementation Details](./BEP-1037/implementation_detail.md) for code-level specifications.

## Further Consideration

### Alerting and Event Notification

When a volume backend transitions to an unhealthy or degraded state, administrators may need to be notified proactively rather than discovering issues through manual queries. Potential approaches include:

- **Event emission**: Emit events to the event system when volume health status changes
- **Webhook integration**: Trigger webhooks for external alerting systems (PagerDuty, Slack, etc.)
- **Admin notification**: Send notifications to domain/system admins when critical storage becomes unavailable

This is out of scope for the initial implementation but should be considered for future enhancements.

## References

- [BEP-1024: Agent RPC Connection Pooling](BEP-1024-agent-rpc-connection-pooling.md) - Similar health check pattern
- [common/health_checker/](../src/ai/backend/common/health_checker/) - Existing HealthProbe infrastructure
- [storage/volumes/abc.py](../src/ai/backend/storage/volumes/abc.py) - `AbstractVolume.get_hwinfo()` interface
