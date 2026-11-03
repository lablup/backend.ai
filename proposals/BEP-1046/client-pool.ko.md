# 클라이언트 풀과 조회 API 세부 사항

> 상위 문서: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## ServiceCatalogCache (클라이언트 측 캐시)

각 컴포넌트는 서비스 디스커버리 backend 가 실패하는 동안에도 기존 연결을 유지하도록 서비스 디스커버리 정보를 로컬 메모리에 캐시한다.

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

## SDClientPool (서비스 디스커버리 기반 클라이언트 풀)

`ServiceCatalogCache` 위에 HTTP/RPC 클라이언트 풀을 구성한다.

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

## 기존 주소 관리의 이행 전략

각 서비스의 주소는 지금 서로 다른 위치에서 관리된다. 서비스 카탈로그로 이행할 때 이런 의존성을 해소해야 한다.

| 서비스 | 현재 주소 저장 위치 | 서비스 디스커버리 이행 방식 |
|---------|------------------------|----------------------|
| **Agent** | `agents` 테이블(`addr` column) | 서비스 카탈로그에서 `role="rpc"` 조회로 대체한다. 서비스 디스커버리 등록 시 `AgentRow.addr` 을 자동 동기화하거나 서비스 디스커버리 조회로 점진적으로 이행한다 |
| **Storage Proxy** | etcd 설정에 주소를 저장 | 서비스 카탈로그에서 `role="api"` 조회로 대체한다. etcd 의존성을 제거한다 |
| **App Proxy coordinator** | `scaling_groups` row 의 `wsproxy_addr`, `wsproxy_api_token` | 서비스 카탈로그에서 `service_group="appproxy-coordinator"` 조회로 대체한다. `scaling_group` 과 app proxy coordinator 의 매핑을 정의해야 한다 |
| **App Proxy worker** | HTTP 요청으로 app proxy coordinator 에 연결 | app proxy worker 와 app proxy coordinator 의 연결은 유지한다. app proxy coordinator 주소만 서비스 디스커버리에서 조회한다 |

> **Note**: App Proxy coordinator 의 `wsproxy_addr` 는 지금 `scaling_group` 마다 지정된다. 서비스 디스커버리로 이행할 때 매핑을 유지하도록 app proxy coordinator 의 레이블에 `scaling_group` 정보를 포함해야 한다. 이 내용은 4단계에서 자세히 설계한다.

## 사용 예시

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

## GraphQL 조회 API

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

- 관리자 전용이며 superadmin 또는 적절한 RBAC 스코프를 요구한다
- `service_group`, `status`, `role`, `scope` 기준 필터를 지원한다
