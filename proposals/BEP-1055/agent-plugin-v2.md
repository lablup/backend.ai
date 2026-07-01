<!-- context-for-ai
type: detail-doc
parent: BEP-1055 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: The runtime-neutral v2 agent network plugin — splits host-level session-network lifecycle from runtime-specific endpoint attach, returning a neutral NetworkAttachSpec.
depends-on: [control-plane.md, data-plane-backends.md]
key-decisions:
  - New plugin group backendai_network_agent_v2; v1 Docker plugins untouched.
  - attach_endpoint returns a runtime-neutral NetworkAttachSpec; provisioners translate it.
-->

# BEP-1055: Runtime-Neutral Agent Plugin (v2)

## Summary

The only Docker coupling in the current design is `AbstractNetworkAgentPlugin.join_network()` returning a Docker container-config dict. v2 introduces a new plugin group that (a) separates **host-level session-network lifecycle** (agent builds vxlan/bridge/routes itself) from **runtime-specific endpoint attach**, and (b) returns a **runtime-neutral `NetworkAttachSpec`** that Docker or containerd provisioners interpret.

## Current Design

- `AbstractNetworkAgentPlugin[TKernel].join_network(kernel_config, cluster_info, *, network_name, **kwargs) -> dict[str, Any]` returns Docker `NetworkMode`/`HostConfig`.
- With Swarm, the network already exists (created by manager); the agent only sets `NetworkMode`. v2 must actively build the data plane, so a single `join_network` call is insufficient.

## Proposed Design

### Runtime-neutral types (`common/network/types.py`)

```python
class AttachKind(StrEnum):
    CNI = "cni"                 # containerd and other CNI runtimes
    DOCKER_NETWORK = "docker"   # v1 back-compat bridge
    HOST_NETNS = "netns"        # agent-driven veth/setns

@dataclass(frozen=True)
class SessionNetMeta:
    session_id: str
    subnet: str
    vni: int | None
    backend: str                # "vxlan" | "host-gw" | "wireguard"
    mtu: int

@dataclass(frozen=True)
class Member:
    agent_id: str
    host_ip: str
    vtep_ip: str | None
    ip_range: str | None

class NetworkRole(StrEnum):
    LOCAL = "local"        # host-local bridge: agent<->container control + egress (ICC disabled)
    OVERLAY = "overlay"    # cross-node cluster network; the isolated per-session L2 domain

@dataclass(frozen=True)
class NetworkAttachSpec:
    kind: AttachKind
    interface_name: str
    role: NetworkRole = NetworkRole.LOCAL
    is_default_route: bool = False
    ip: str | None = None
    cni_config: Mapping[str, Any] | None = None
    docker_config: Mapping[str, Any] | None = None
    netns_ops: Mapping[str, Any] | None = None

@dataclass(frozen=True)
class EndpointPlan:
    """Ordered interface chain for one container.
    Invariants: exactly one LOCAL attachment; multi-node adds exactly one OVERLAY;
    at most one is_default_route (normally LOCAL)."""
    attachments: list[NetworkAttachSpec]

@dataclass(frozen=True)
class AgentNetworkCaps:
    tunnel_offload: bool
    native_routing_ok: bool
    backends: list[str]
```

### Plugin interface (`agent/plugin/network_v2.py`, group `backendai_network_agent_v2`)

```python
class AbstractNetworkAgentPluginV2[TKernel: AbstractKernel](AbstractPlugin, metaclass=ABCMeta):
    # capability probe drives control-plane backend selection
    async def probe_caps(self) -> AgentNetworkCaps: ...

    # host-level session-network lifecycle (runtime-neutral)
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None: ...
    async def teardown_session_network(self, session_id: str) -> None: ...
    async def add_peer(self, session_id: str, peer: Member) -> None: ...   # fdb / route
    async def del_peer(self, session_id: str, peer: Member) -> None: ...

    # runtime-specific endpoint attach, described neutrally
    async def attach_endpoint(
        self, kernel_config: KernelCreationConfig, cluster_info: ClusterInfo,
        *, meta: SessionNetMeta,
    ) -> EndpointPlan: ...   # always one LOCAL; multi-node adds one OVERLAY
    async def detach_endpoint(self, kernel: TKernel) -> None: ...

    async def get_capabilities(self) -> set[ContainerNetworkCapability]:  # GLOBAL/port-forward, as v1
        return set()

class NetworkPluginContextV2(BasePluginContext[AbstractNetworkAgentPluginV2[Any]]):
    plugin_group = "backendai_network_agent_v2"
```

### Provisioner consumption

The provisioner iterates `EndpointPlan.attachments` in order:

| Runtime | Provisioner | Interprets |
|---------|-------------|-----------|
| Docker | `stage/kernel_lifecycle/docker/network.py` (extended) | each `docker_config` → HostConfig/NetworkingConfig (reproduces v1) |
| containerd | `stage/kernel_lifecycle/containerd/network.py` (new) | each `cni_config` → CNI ADD into the container netns, as a chain |

The same v2 backend (e.g. `vxlan`) thus attaches under both runtimes; runtime specifics live only in the provisioner. The LOCAL attachment (agent control + egress, ICC-disabled) carries the default route and is always present; the OVERLAY attachment (multi-node only) carries inter-node isolation and installs only the session-subnet route.

### Peer synchronization ownership

A per-session, runtime-neutral **`SessionNetworkCoordinator`** (agent-side) owns the membership lifecycle; the v2 plugin is a stateless data-plane executor that never starts its own watch:

```
SessionNetworkCoordinator (per session)
  read meta -> plugin.setup_session_network()
  write members/{self}=ready
  watch network/session/{sid}/members/ -> plugin.add_peer() / plugin.del_peer()
  barrier on all-ready -> allow container start
  teardown -> plugin.teardown_session_network()

NetworkProvisioner (per container, runtime-specific)
  plugin.attach_endpoint() -> interpret NetworkAttachSpec
```

Rationale (Decision Log, 2026-07-01): the watch/reconcile loop is backend-invariant and session-scoped, so centralizing it avoids per-backend duplication and keeps it out of the per-container provisioner. Backend-specific behavior remains in the idempotent `add_peer`/`del_peer`.

## Interface / API

Public surface = the types above + `AbstractNetworkAgentPluginV2` + `NetworkPluginContextV2`. Backends implement the plugin; provisioners consume `NetworkAttachSpec`. Peer-sync ownership (plugin-internal watch vs provisioner-driven) is an Open Question resolved in P2.

## Implementation Notes

- Per `agent/CLAUDE.md`: runtime-specific code stays under `agent/docker/` and `agent/containerd/`; the abstract base and neutral types live in `agent/plugin/` and `common/network/`.
- v1 remains registered and default; v2 is additive. No change to Docker behavior until `default_driver="cni"`.
- Container state changes still flow through the `agent/stage/` lifecycle; attach happens within the provisioner stage, not via ad-hoc calls.
