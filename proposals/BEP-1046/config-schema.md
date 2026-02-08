# Config Schema Details

> Parent document: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## TOML Config Examples

Add a `[service-discovery]` section to each component's TOML config.

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

## Pydantic Models

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

## instance_id Strategy

`instance_id` is a **stable business identifier** that must persist across service restarts. Upserts are performed using the `(service_group, instance_id)` pair.

### Per-Component Rules

| Component | instance_id Resolution | Example |
|-----------|----------------------|---------|
| Agent | SD config `instance-id` first, falls back to `agent_id` | `i-host-a` |
| Manager | config `instance-id` or auto-generate `manager-{uuid4()}` | `manager-abc123` |
| Storage Proxy | config `instance-id` required (multi-instance distinction) | `storage-nfs-01` |
| AppProxy Coordinator | config `instance-id` required (multi-instance distinction) | `coordinator-zone-a` |
| AppProxy Worker | config `instance-id` or auto-generate `worker-{uuid4()}` | `worker-abc123` |
| Webserver | config `instance-id` or auto-generate `webserver-{uuid4()}` | `webserver-abc123` |

### Auto-Generation Code

Follows the `defaulted_id` pattern. SD config's `instance-id` takes highest priority; component-specific fallback is applied if absent.

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

> **Note**: When auto-generated, a new UUID is issued on every process restart, so existing records won't match. In this case, previous records expire via heartbeat timeout (UNHEALTHY → natural cleanup) and a new record is created. Services requiring stable identification (Storage Proxy, AppProxy Coordinator, etc.) must explicitly set `instance-id` in config.
