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

When users perform vfolder operations, the volume host of the storage proxy hosting that vfolder may be unreachable. Currently, there is no way to check this in advance, so users only become aware of the issue when the operation fails.

**Problems:**
- Cannot immediately determine if vfolder operation failure is due to volume host inaccessibility
- Administrators cannot query the status of a specific volume host via API
- Users cannot check the availability of the storage their vfolder uses in advance

The storage proxy already provides a `/manager-api/health` endpoint, but the Manager does not utilize it.

## Current Design

### Storage Proxy Health Endpoint

The storage proxy exposes health status via `/manager-api/health` endpoint:

```python
# storage-proxy health endpoint
GET /manager-api/health
Response: {
    "status": "healthy" | "degraded" | "unhealthy",
    "version": "...",
    ...
}
```

### Current Manager State

- No health check method in `StorageProxyManagerFacingClient`
- `HealthProbe` only monitors Database, Etcd, and Valkey; storage proxy is not included
- No way to query volume host status via GraphQL API

## Proposed Design

### 1. Add Health Check Method (BA-3981)

Add `check_health()` method to `StorageProxyManagerFacingClient`:

```python
# manager/clients/storage_proxy/manager_facing_client.py
class StorageProxyManagerFacingClient:
    async def check_health(self, timeout: float = 10.0) -> HealthResponse:
        """Call the storage proxy's /health endpoint to check status."""
        async with asyncio.timeout(timeout):
            async with self._session.get(
                self._build_url("/health"),
                headers=self._build_headers(),
            ) as resp:
                data = await resp.json()
                return HealthResponse.model_validate(data)
```

**Impact:**
| File | Changes |
|------|---------|
| `manager/clients/storage_proxy/manager_facing_client.py` | Add `check_health()` method |

### 2. Implement StorageProxyHealthChecker (BA-3982)

Periodically check volume host status using existing `HealthProbe` infrastructure:

```python
# common/health_checker/types.py
class ServiceGroup(StrEnum):
    DATABASE = "database"
    ETCD = "etcd"
    VALKEY = "valkey"
    STORAGE_PROXY = "storage_proxy"  # Add

# manager/health/storage_proxy.py
class StorageProxyHealthChecker(StaticServiceHealthChecker):
    """Check volume host accessibility for all configured storage proxies."""

    @property
    def service_group(self) -> ServiceGroup:
        return ServiceGroup.STORAGE_PROXY

    async def check_service(self) -> ServiceHealth:
        components: dict[str, ComponentHealthStatus] = {}

        for proxy_name, proxy_client in self._storage_manager.iter_proxies():
            try:
                health = await proxy_client.check_health(timeout=self._timeout)
                components[proxy_name] = ComponentHealthStatus(
                    status=health.status,
                    is_healthy=health.is_healthy,
                    last_checked_at=datetime.now(timezone.utc),
                    error_message=None,
                )
            except Exception as e:
                components[proxy_name] = ComponentHealthStatus(
                    status=HealthStatus.UNHEALTHY,
                    is_healthy=False,
                    last_checked_at=datetime.now(timezone.utc),
                    error_message=str(e),
                )

        return ServiceHealth(
            service_group=ServiceGroup.STORAGE_PROXY,
            components=components,
        )
```

**Impact:**
| File | Changes |
|------|---------|
| `common/health_checker/types.py` | Add `STORAGE_PROXY` constant |
| `manager/health/storage_proxy.py` | New file: `StorageProxyHealthChecker` |
| `manager/health/BUILD` | Add build target |
| `manager/server.py` | Register checker in `health_probe_ctx` |

### 3. Add GraphQL Query (BA-3983)

Add GraphQL query for volume host status:

```python
# manager/api/gql/storage_health/types.py
@strawberry.enum
class StorageHealthStatusEnum(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

@strawberry.type
class StorageProxyHealth:
    proxy_name: str
    status: StorageHealthStatusEnum
    is_healthy: bool
    last_checked_at: datetime | None
    error_message: str | None
```

**GraphQL Query Example:**
```graphql
query {
  storageProxyHealthList {
    proxyName
    status
    isHealthy
    lastCheckedAt
    errorMessage
  }
}
```

**Impact:**
| File | Changes |
|------|---------|
| `manager/api/gql/storage_health/__init__.py` | New package |
| `manager/api/gql/storage_health/types.py` | GraphQL type definitions |
| `manager/api/gql/storage_health/resolver.py` | Query resolver |
| `manager/api/gql/storage_health/BUILD` | Build target |
| `manager/api/gql/schema.py` | Register query |

### 4. Add storageHealth Field to VFolder (BA-3984)

Allow users to check storage status when querying vfolder:

```python
# manager/api/gql/vfolder.py
@strawberry.type
class VirtualFolderNode:
    # ... existing fields ...

    @strawberry.field
    async def storage_health(self, info: Info) -> StorageProxyHealth | None:
        """Return the status of the volume host hosting this vfolder."""
        if self.host is None:
            return None

        proxy_name, _ = root_ctx.storage_manager.get_proxy_and_volume(self.host)
        # Query proxy status from HealthProbe and return
        ...
```

**GraphQL Query Example:**
```graphql
query {
  vfolderNode(id: "...") {
    name
    host
    storageHealth {
      status
      isHealthy
    }
  }
}
```

**Impact:**
| File | Changes |
|------|---------|
| `manager/api/gql/vfolder.py` | Add `storageHealth` field |

### 5. Tests (BA-3985)

| Test File | Content |
|-----------|---------|
| `tests/manager/health/test_storage_proxy.py` | `StorageProxyHealthChecker` unit tests |
| `tests/manager/api/gql/test_storage_health.py` | GraphQL resolver tests |

**Test Scenarios:**
1. All proxies return healthy when all are accessible
2. Only the specific proxy returns unhealthy when some proxies are unreachable
3. Health check timeout handling
4. `storageProxyHealthList` query returns correct results
5. `VirtualFolderNode.storageHealth` field returns correct proxy status

## Migration / Compatibility

- **Backward compatible**: All changes are additive, no impact on existing APIs
- `storageHealth` field is nullable, so no client updates required

## Implementation Plan

| Phase | Issue | Work |
|-------|-------|------|
| 1 | BA-3981 | Add `check_health()` method |
| 2 | BA-3982 | Implement and register `StorageProxyHealthChecker` |
| 3 | BA-3983 | Add GraphQL `storageProxyHealthList` query |
| 4 | BA-3984 | Add `VirtualFolderNode.storageHealth` field |
| 5 | BA-3985 | Write tests |

## Open Questions

1. ~~**`storageProxyHealthList` permission**~~: Both admins and regular users should be able to query storage health status.

2. ~~**Health check interval**~~: A separate configuration for storage proxy health check interval is required, independent from the default `HealthProbe` interval.

## References

- [BEP-1024: Agent RPC Connection Pooling](BEP-1024-agent-rpc-connection-pooling.md) - Similar health check pattern
- [common/health_checker/](../src/ai/backend/common/health_checker/) - Existing HealthProbe infrastructure
