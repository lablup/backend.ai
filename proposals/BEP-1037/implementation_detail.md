# BEP-1037 Implementation Details

This document contains detailed implementation specifications for [BEP-1037: Volume Host Availability Check](../BEP-1037-storage-proxy-health-monitoring.md).

## Table of Contents

1. [Storage Proxy Health Endpoint Extension](#1-storage-proxy-health-endpoint-extension)
2. [Manager Client Methods](#2-manager-client-methods)
3. [StorageHealthChecker Implementation](#3-storagehealthchecker-implementation)
4. [GraphQL Types and Resolvers](#4-graphql-types-and-resolvers)
5. [VFolder storageHealth Field](#5-vfolder-storagehealth-field)
6. [Configuration](#6-configuration)
7. [Test Scenarios](#7-test-scenarios)

---

## 1. Storage Proxy Health Endpoint Extension

### Code Changes

```python
# storage/api/manager.py - Extended health endpoint
GET /manager-api/health
Response: {
    "status": "healthy" | "unhealthy",
    "version": "...",
    "volumes": {
        "volume1": {
            "status": "healthy" | "degraded" | "offline" | "unavailable",
            "status_info": "GPFS cluster healthy, 8/8 nodes online",
            "backend": "gpfs",
            "last_checked_at": "2026-01-22T10:00:00Z"
        },
        "volume2": {
            "status": "degraded",
            "status_info": "Ceph cluster degraded: 2 OSDs down",
            "backend": "cephfs",
            "last_checked_at": "2026-01-22T10:00:00Z"
        }
    }
}
```

### Impact

| File | Changes |
|------|---------|
| `storage/api/manager.py` | Extend health endpoint response |
| `storage/server.py` | Add background health check task |
| `storage/types.py` | Add `VolumeHealthInfo` type |
| `storage/config.py` | Add `health_check_interval` config option |

---

## 2. Manager Client Methods

### Code Changes

```python
# manager/clients/storage_proxy/manager_facing_client.py
class StorageProxyManagerFacingClient:
    async def check_proxy_health(self, timeout: float = 10.0) -> ProxyHealthResponse:
        """Check if the storage proxy service is responding."""
        async with asyncio.timeout(timeout):
            async with self._session.get(
                self._build_url("/health"),
                headers=self._build_headers(),
            ) as resp:
                data = await resp.json()
                return ProxyHealthResponse.model_validate(data)

    async def get_volume_health(
        self, volume_id: str, timeout: float = 10.0
    ) -> VolumeHealthResponse:
        """Get health status of a specific volume backend."""
        async with asyncio.timeout(timeout):
            async with self._session.get(
                self._build_url(f"/volumes/{volume_id}/health"),
                headers=self._build_headers(),
            ) as resp:
                data = await resp.json()
                return VolumeHealthResponse.model_validate(data)
```

### Impact

| File | Changes |
|------|---------|
| `manager/clients/storage_proxy/manager_facing_client.py` | Add health check methods |
| `manager/clients/storage_proxy/types.py` | Add response types |

---

## 3. StorageHealthChecker Implementation

### Code Changes

Storage Proxy health and Volume Backend health are tracked independently:

```python
# manager/health/storage.py
class StorageHealthChecker:
    """Check health of storage proxies and their volume backends independently."""

    async def check_proxies(self) -> dict[str, ProxyHealthStatus]:
        """Check if each storage proxy service is responding."""
        results: dict[str, ProxyHealthStatus] = {}

        for proxy_name, proxy_client in self._storage_manager.iter_proxies():
            try:
                await proxy_client.check_proxy_health(timeout=self._timeout)
                results[proxy_name] = ProxyHealthStatus(
                    status=HealthStatus.HEALTHY,
                    is_healthy=True,
                    last_checked_at=datetime.now(timezone.utc),
                    error_message=None,
                )
            except Exception as e:
                results[proxy_name] = ProxyHealthStatus(
                    status=HealthStatus.UNHEALTHY,
                    is_healthy=False,
                    last_checked_at=datetime.now(timezone.utc),
                    error_message=str(e),
                )

        return results

    async def check_volumes(self) -> dict[str, VolumeHealthStatus]:
        """Check health of each volume backend."""
        results: dict[str, VolumeHealthStatus] = {}

        for proxy_name, proxy_client in self._storage_manager.iter_proxies():
            try:
                proxy_health = await proxy_client.check_proxy_health(timeout=self._timeout)
            except Exception:
                # Proxy unreachable - skip volume checks for this proxy
                continue

            for volume_id, volume_health in proxy_health.volumes.items():
                key = f"{proxy_name}:{volume_id}"
                results[key] = VolumeHealthStatus(
                    status=volume_health.status,
                    is_healthy=volume_health.status == "healthy",
                    backend=volume_health.backend,
                    status_info=volume_health.status_info,
                    last_checked_at=volume_health.last_checked_at,
                )

        return results
```

### Impact

| File | Changes |
|------|---------|
| `manager/health/storage.py` | New file: `StorageHealthChecker` |
| `manager/health/BUILD` | Add build target |
| `manager/server.py` | Register checker in `health_probe_ctx` |

---

## 4. GraphQL Types and Resolvers

### Type Definitions

```python
# manager/api/gql/storage_health/types.py

# Proxy health status (simple: healthy or unhealthy)
@strawberry.enum
class ProxyHealthStatusEnum(Enum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"

# Volume backend health status (matches HardwareMetadata.status)
@strawberry.enum
class VolumeHealthStatusEnum(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"  # When proxy is unreachable

@strawberry.type
class VolumeHealth:
    """Health status of a storage volume backend."""
    proxy_name: str
    volume_id: str
    backend_type: str  # "gpfs", "cephfs", "vfs", etc.
    status: VolumeHealthStatusEnum
    status_info: str | None
    is_healthy: bool
    last_checked_at: datetime | None

@strawberry.type
class StorageProxyHealth:
    """Health status of a storage proxy."""
    proxy_name: str
    status: ProxyHealthStatusEnum
    is_healthy: bool
    last_checked_at: datetime | None
    error_message: str | None
```

### Impact

| File | Changes |
|------|---------|
| `manager/api/gql/storage_health/__init__.py` | New package |
| `manager/api/gql/storage_health/types.py` | GraphQL type definitions |
| `manager/api/gql/storage_health/resolver.py` | Query resolver |
| `manager/api/gql/storage_health/BUILD` | Build target |
| `manager/api/gql/schema.py` | Register query |

---

## 5. VFolder storageHealth Field

### Code Changes

```python
# manager/api/gql/vfolder.py
@strawberry.type
class VirtualFolderNode:
    # ... existing fields ...

    @strawberry.field
    async def storage_health(self, info: Info) -> VolumeHealth | None:
        """Return the health status of the volume backend hosting this vfolder."""
        if self.host is None:
            return None

        root_ctx = info.context
        proxy_name, volume_id = root_ctx.storage_manager.split_host(self.host)

        # Query volume health from cache
        volume_health = root_ctx.health_checker.get_volume_health(
            f"{proxy_name}:{volume_id}"
        )

        if volume_health is None:
            return VolumeHealth(
                proxy_name=proxy_name,
                volume_id=volume_id,
                backend_type="unknown",
                status=VolumeHealthStatusEnum.UNKNOWN,
                status_info=None,
                is_healthy=False,
                last_checked_at=None,
            )

        return VolumeHealth(
            proxy_name=proxy_name,
            volume_id=volume_id,
            backend_type=volume_health.backend,
            status=VolumeHealthStatusEnum(volume_health.status.upper()),
            status_info=volume_health.status_info,
            is_healthy=volume_health.is_healthy,
            last_checked_at=volume_health.last_checked_at,
        )
```

### Impact

| File | Changes |
|------|---------|
| `manager/api/gql/vfolder.py` | Add `storageHealth` field |

---

## 6. Configuration

### Storage Proxy Configuration

```toml
# storage-proxy.toml
[volume.local]
backend = "vfs"
path = "/data/local"
health_check_interval = "30s"  # Default: 30s

[volume.gpfs-cluster]
backend = "gpfs"
path = "/gpfs/scratch"
health_check_interval = "5m"  # Longer interval for GPFS

[volume.ceph-storage]
backend = "cephfs"
path = "/mnt/cephfs"
health_check_interval = "1m"
```

---

## 7. Test Scenarios

### Test Files

| Test File | Content |
|-----------|---------|
| `tests/storage/api/test_health.py` | Extended health endpoint tests |
| `tests/manager/health/test_storage.py` | `StorageHealthChecker` unit tests |
| `tests/manager/api/gql/test_storage_health.py` | GraphQL resolver tests |

### Proxy Health Tests

- Proxy responds HEALTHY when service is up
- Proxy returns UNHEALTHY when service is down

### Volume Backend Health Tests

- GPFS volume returns healthy when cluster is healthy
- GPFS volume returns degraded when some nodes are down
- Ceph volume returns degraded when OSDs are down
- Ceph volume returns offline when cluster is unreachable
- VFS volume returns healthy when filesystem is accessible
- NetApp volume returns unavailable when API is unreachable

### Combined Tests

- All volumes healthy when proxy and all backends are up
- Specific volumes offline when their backends are down
- Volume status unknown when proxy is unreachable

### GraphQL Tests

- `storageProxyHealthList` returns correct proxy status
- `volumeHealthList` returns correct volume status
- `VirtualFolderNode.storageHealth` returns correct backend status
