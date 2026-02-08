# Client Pool & Query API Details

> Parent document: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## ServiceCatalogCache (Client-side Cache)

Each component caches SD information in local memory to maintain existing connections even during SD backend failures.

```python
class ServiceCatalogCache:
    """
    Applies Consul agent cache + Eureka client registry patterns.
    """
    _cache: dict[str, list[ServiceEntry]]   # service_group → entries
    _last_sync: float
    _frozen: bool                            # self-preservation mode

    async def full_fetch(self) -> None:
        """Load full catalog on startup"""
        try:
            entries = await self._fetch_from_manager("/sd/catalog")
            self._cache = group_by(entries, key=lambda e: e.service_group)
            self._frozen = False
        except ConnectionError:
            self._load_from_snapshot()   # Restore from previous snapshot

    async def delta_sync(self) -> None:
        """Periodic incremental sync"""
        try:
            changes = await self._fetch_delta()
            self._apply_changes(changes)
            self._frozen = False
        except ConnectionError:
            self._enter_self_preservation()

    def _enter_self_preservation(self) -> None:
        """Eureka self-preservation: freeze state on backend failure"""
        self._frozen = True
        # Keep existing cache, do not evict services

    def get_endpoints(
        self,
        service_group: str,
        role: str,
        scope: str | None = None,
    ) -> list[ServiceEndpointInfo]:
        """Query endpoints by role + scope"""
        entries = self._cache.get(service_group, [])
        result = []
        for entry in entries:
            for ep in entry.endpoints:
                if ep.role == role and (scope is None or ep.scope == scope):
                    result.append(ep)
        return result
```

## SDClientPool (SD-based Client Pool)

Builds HTTP/RPC client pool on top of `ServiceCatalogCache`.

```python
class SDClientPool:
    """Auto-managed client pool based on ServiceCatalogCache"""

    def __init__(
        self,
        catalog_cache: ServiceCatalogCache,
        service_group: str,
        role: str,
        scope: str,
    ):
        self._cache = catalog_cache
        self._group = service_group
        self._role = role
        self._scope = scope
        self._clients: dict[UUID, ClientSession] = {}

    async def get_client(self) -> ClientSession:
        """Select healthy service from cache → return client"""
        endpoints = self._cache.get_endpoints(
            self._group, self._role, self._scope
        )
        selected = self._load_balance(endpoints)
        return self._get_or_create_client(selected)

    async def sync(self) -> None:
        """Update pool on cache changes"""
        current = {ep.instance_id for ep in
                   self._cache.get_endpoints(self._group, self._role, self._scope)}
        # Clean up removed services
        for sid in list(self._clients):
            if sid not in current:
                await self._clients.pop(sid).close()
```

## Existing Address Management Transition Strategy

Each service's address is currently managed in different locations. These dependencies must be resolved when transitioning to the SD catalog:

| Service | Current Address Storage | SD Transition Approach |
|---------|------------------------|----------------------|
| **Agent** | `agents` table (`addr` column) | Replace with `role="rpc"` query from SD catalog. Auto-sync `AgentRow.addr` on SD registration, or gradually transition to SD queries |
| **Storage Proxy** | Address stored in etcd config | Replace with `role="api"` query from SD catalog. Remove etcd dependency |
| **AppProxy Coordinator** | `wsproxy_addr`, `wsproxy_api_token` in `scaling_groups` row | Replace with `service_group="appproxy-coordinator"` query from SD catalog. Need to define scaling_group-to-coordinator mapping |
| **AppProxy Worker** | Connects via HTTP request to Coordinator | Maintain Worker → Coordinator relationship. Only resolve Coordinator address from SD |

> **Note**: For AppProxy Coordinator, `wsproxy_addr` is currently specified per scaling_group. When transitioning to SD, the coordinator's labels should include `scaling_group` information to maintain the mapping relationship. This will be designed in detail during Phase 4.

## Usage Examples

```python
# Manager requesting Storage Proxy
storage_pool = SDClientPool(
    catalog_cache, "storage-proxy", role="api", scope="cluster"
)
client = await storage_pool.get_client()
await client.post("/volumes/create", ...)

# Manager calling Agent RPC
# Replace AgentClientPool's address resolution with SD-based
agent_endpoints = catalog_cache.get_endpoints("agent", role="rpc", scope="cluster")
```

## GraphQL Query API

```graphql
query {
    service_catalog(
        service_group: "storage-proxy"
        status: HEALTHY
    ) {
        id
        service_group
        display_name
        version
        status
        registered_at
        last_heartbeat
        labels
        endpoints {
            role
            scope
            address
            port
            protocol
            metadata
        }
    }
}
```

- Admin-only (requires superadmin or appropriate RBAC scope)
- Supports filtering by `service_group`, `status`, `role`, `scope`
