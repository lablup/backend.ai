# Config schema 상세

> 상위 문서: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## TOML 설정 예시

각 컴포넌트의 TOML config 에 `[service-discovery]` 절을 추가한다.

### Agent

```toml
[service-discovery]
# instance-id = "i-host-a"         # Falls back to agent_id if omitted
# service-group = "agent"          # Auto-detected from component name if omitted
# display-name = "agent-node01"    # Auto-generated if omitted

[service-discovery.extra-labels]
# zone = "ap-northeast-2a"

[[service-discovery.endpoints]]
role = "rpc"
scope = "cluster"
address = "10.0.1.5"
port = 6001
protocol = "zmq"

[[service-discovery.endpoints]]
role = "metrics"
scope = "cluster"
address = "10.0.1.5"
port = 6002
protocol = "http"

[[service-discovery.endpoints]]
role = "metrics"
scope = "container"
address = "host.docker.internal"
port = 6002
protocol = "http"
```

### Storage Proxy

```toml
[service-discovery]
instance-id = "storage-nfs-01"     # Required for multi-instance distinction

[[service-discovery.endpoints]]
role = "api"
scope = "cluster"
address = "storage.internal"
port = 6022
protocol = "http"

[[service-discovery.endpoints]]
role = "client-api"
scope = "cluster"
address = "storage.internal"
port = 6021
protocol = "http"

[[service-discovery.endpoints]]
role = "client-api"
scope = "container"
address = "host.docker.internal"
port = 6023
protocol = "http"
```

## Pydantic 모델

```python
# src/ai/backend/common/configs/service_discovery.py

class ServiceEndpointConfig(BaseConfigSchema):
    role: Annotated[str, Field(...),
        BackendAIConfigMeta(
            description="Endpoint role identifier (e.g., api, rpc, metrics)",
            added_version="26.3.0",
        )]
    scope: Annotated[str, Field(...),
        BackendAIConfigMeta(
            description="Network scope: cluster, container, public",
            added_version="26.3.0",
        )]
    address: Annotated[str, Field(...),
        BackendAIConfigMeta(
            description="Endpoint host address or IP",
            added_version="26.3.0",
        )]
    port: Annotated[int, Field(...),
        BackendAIConfigMeta(
            description="Endpoint port number",
            added_version="26.3.0",
        )]
    protocol: Annotated[str, Field(...),
        BackendAIConfigMeta(
            description="Protocol: http, zmq, rpc, ws, grpc",
            added_version="26.3.0",
        )]
    metadata: Annotated[dict[str, str], Field(default_factory=dict),
        BackendAIConfigMeta(
            description="Additional endpoint metadata",
            added_version="26.3.0",
            composite=CompositeType.DICT,
        )]

class ServiceDiscoveryConfig(BaseConfigSchema):
    instance_id: Annotated[str | None, Field(default=None),
        BackendAIConfigMeta(
            description="Stable instance identifier, unique within service_group. "
                        "Auto-generated as '{service_group}-{uuid4}' if omitted. "
                        "For agents, falls back to agent_id.",
            added_version="26.3.0",
        )]
    service_group: Annotated[str | None, Field(default=None),
        BackendAIConfigMeta(
            description="Service group name. Auto-detected from component if omitted.",
            added_version="26.3.0",
        )]
    display_name: Annotated[str | None, Field(default=None),
        BackendAIConfigMeta(
            description="Human-readable service name. Auto-generated if omitted.",
            added_version="26.3.0",
        )]
    extra_labels: Annotated[dict[str, str], Field(default_factory=dict),
        BackendAIConfigMeta(
            description="Additional labels for filtering and metadata",
            added_version="26.3.0",
            composite=CompositeType.DICT,
        )]
    endpoints: Annotated[list[ServiceEndpointConfig], Field(default_factory=list),
        BackendAIConfigMeta(
            description="Service endpoints with role and scope",
            added_version="26.3.0",
            composite=CompositeType.LIST,
        )]
```

## instance_id 전략

`instance_id` 는 컴포넌트가 재시작해도 유지되어야 하는 **안정적인 업무 식별자** 이다. `(service_group, instance_id)` 쌍으로 저장한다(upsert).

### 컴포넌트별 규칙

| 컴포넌트 | instance_id 결정 | 예시 |
|-----------|----------------------|---------|
| Agent | 서비스 디스커버리 config 의 `instance-id`, 없으면 `agent_id` | `i-host-a` |
| Manager | config 의 `instance-id`, 없으면 `manager-{uuid4()}` 자동 생성 | `manager-abc123` |
| Storage Proxy | config 의 `instance-id` 가 필수다. 다중 instance 를 구분한다 | `storage-nfs-01` |
| App Proxy Coordinator | config 의 `instance-id` 가 필수다. 다중 instance 를 구분한다 | `coordinator-zone-a` |
| App Proxy Worker | config 의 `instance-id`, 없으면 `worker-{uuid4()}` 자동 생성 | `worker-abc123` |
| Webserver | config 의 `instance-id`, 없으면 `webserver-{uuid4()}` 자동 생성 | `webserver-abc123` |

### 자동 생성 코드

`defaulted_id` 패턴을 따른다. 서비스 디스커버리 config 의 `instance-id` 가 가장 높은 우선순위를 가지고, 없으면 컴포넌트별 fallback 을 적용한다.

```python
@property
def defaulted_instance_id(self) -> str:
    # Priority 1: SD config instance-id
    if self.service_discovery.instance_id:
        return self.service_discovery.instance_id
    # Priority 2: Component-specific fallback (e.g., agent_id for Agent)
    if self._component_id:
        return self._component_id
    # Priority 3: Auto-generate
    return f"{self.service_group}-{uuid4()}"
```

> **Note**: 자동 생성하면 process 가 재시작될 때마다 새 UUID 가 발급되어 기존 record 와 맞지 않는다. 이 경우 이전 record 는 서비스 카탈로그 heartbeat 시간 초과로 만료된다. 상태가 UNHEALTHY 가 되면 자동으로 정리되고, 새 record 를 생성한다. Storage Proxy, App Proxy Coordinator 처럼 안정적인 식별이 필요한 컴포넌트는 config 에 `instance-id` 를 직접 설정해야 한다.
