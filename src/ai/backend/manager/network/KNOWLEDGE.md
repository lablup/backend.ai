---
name: manager-cluster-network
type: design-rationale
description: The manager's cluster-network seam — which driver serves a session (driver/backend pairing, the Swarm overlay fallback) and where the network plugins plug in
scope: src/ai/backend/manager/network
keywords: [compatible_backends, endpoint_ips, cluster_network_ip, cluster_hostname_of, resolve_driver_for_agents, require_members_can_serve_driver, OverlayNetworkPlugin, AbstractNetworkManagerPlugin]
sources:
  - src/ai/backend/manager/network/pairing.py
  - src/ai/backend/manager/network/overlay.py
  - src/ai/backend/manager/plugin/network.py
  - src/ai/backend/manager/sokovan/scheduler/launcher/launcher.py
  - src/ai/backend/manager/sokovan/scheduler/hooks/status.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-13
status: stable
---

# Manager cluster network — Knowledge

The manager picks a session's network driver and hands the session to that driver's plugin
(`backendai_network_manager_v1`). `overlay` (Docker Swarm) ships here; a `cni` controller ships as a
plugin. The network config it returns names the agent-side CNI plugin in `type`, and the agent
hands it to that plugin unread; per-kernel addresses go out as `cluster_network_ip`.

## Driver and backend pairing (`pairing.py`)

Each manager network plugin declares `compatible_backends`, the agent backends it can network
(`None` = not checked). `overlay` declares `docker`.

- Resolution keeps the configured driver if it serves the members' published backend; otherwise it takes a plugin that declares that backend, `overlay` first.
- The launcher refuses a member whose published backend the chosen plugin does not declare, before calling `create_network`: a non-Swarm agent under `overlay` would put every kernel on a node-local bridge with no error.
- Mixed runtimes in one session fail (`NetworkBackendMismatch`); missing backend keys pass (agents of releases that publish none).
- Teardown resolves the driver the same way, so the plugin that created the network destroys it.

## What the launcher hands a plugin (`launcher.py`)

| To `create_network` (`options`) | Back from it |
|---|---|
| `member_agents`: the session's agent ids | `options` → the session's `network_config`, sent to every agent |
| `endpoints`: one per kernel (`container_id` = kernel id, `agent_id`, `cluster_hostname`) | `options["endpoint_ips"]`: kernel id → address, popped out of `network_config` |

- `endpoint_ips` goes to each kernel alone, as `cluster_network_ip` in its creation config; the Swarm overlay returns none.
- `cluster_hostname_of` is the one derivation of a kernel's hostname, for `BACKENDAI_CLUSTER_HOST(S)` and `endpoints`: drift between them sends a kernel's own name to loopback.
