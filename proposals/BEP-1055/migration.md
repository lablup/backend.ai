<!-- context-for-ai
type: detail-doc
parent: BEP-1055 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: Rollout, backward compatibility, and the two config switches (default_driver, forced_backend).
depends-on: [control-plane.md, agent-plugin-v2.md]
key-decisions:
  - v1 Docker path untouched; opt-in via default_driver="cni".
  - forced_backend pins a data plane; unset means capability-based auto-selection.
-->

# BEP-1055: Migration & Compatibility

## Summary

The v2 path is additive and opt-in. Existing Docker/Swarm deployments keep running unchanged; a deployment moves to the containerd/CNI path by flipping one config value, and can roll back the same way.

## Config switches (`manager/config/unified.py::InterContainerNetworkConfig`)

```python
class InterContainerNetworkConfig:
    default_driver: str | None = "overlay"   # existing: "overlay" (v1 Swarm) | "cni" (v2)
    forced_backend: str | None = None        # new: "vxlan" | "host-gw" | "wireguard" | None
```

| Setting | Effect |
|---------|--------|
| `default_driver="overlay"` | Current behavior (Swarm). No change. |
| `default_driver="cni"` | v2 control plane + runtime-neutral agent plugin. |
| `forced_backend=None` | Capability-based per-session selection (`host-gw` if all members native-capable, else `vxlan`). |
| `forced_backend="vxlan"` | Pin every session to vxlan (portable, predictable). |

## Backward compatibility

- v1 plugin groups (`backendai_network_manager_v1`, `backendai_network_agent_v1`) and `OverlayNetworkPlugin` remain registered and default.
- No etcd keys under `network/…` are read by the v1 path, so enabling v2 on a subset of scaling groups is safe.
- Docker agents can keep using v1 while containerd agents use v2; a session is scheduled onto a homogeneous set per scaling group.

## Rollout

1. Ship P1 (types, v2 base, config, skeleton) — inert; no behavior change.
2. Enable `default_driver="cni"` + `forced_backend="vxlan"` on a canary scaling group; verify 2-node connectivity and isolation.
3. Enable capability-based selection (`forced_backend=None`) where native routing is proven by probe.
4. Introduce containerd agents in the canary group; Docker groups stay on v1.
5. Broaden per scaling group; keep `overlay` as the documented rollback.

## Breaking changes

- None for existing deployments. New behavior is gated entirely by `default_driver="cni"`.
