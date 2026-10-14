---
name: agent-container-network
type: design-rationale
description: The agent's runtime side of container networking — the CNI plugin contract (ADD, DEL, STATUS, GC) and where the agent calls it, the start gate a Docker container waits at for its ADD, container nameservers, and the container locator a plugin's privileged helper uses
scope: src/ai/backend/agent/network
keywords: [AbstractCniPlugin, CniPluginContext, allow-cni-plugins, CniHostContext, CniRequest, CniResult, not_serving_reason, publish_backend, resolve_container_dns, ContainerLocator, LiveContainer, build_container_locator, stage_gate, apply_gate, wait_gated_pid, repl_host, PUBLISHED_PORTS, cluster_network_ip]
sources:
  - src/ai/backend/agent/network/cni.py
  - src/ai/backend/agent/plugin/cni.py
  - src/ai/backend/agent/network/advert.py
  - src/ai/backend/agent/network/dns.py
  - src/ai/backend/agent/network/locator.py
  - src/ai/backend/agent/network/locator_builder.py
  - src/ai/backend/agent/docker/locator.py
  - src/ai/backend/agent/gate.py
  - src/ai/backend/agent/docker/gate.py
  - src/ai/backend/agent/docker/agent.py
  - src/ai/backend/agent/types.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-13
status: stable
---

# Agent container networking (runtime side) — Knowledge

The agent is the CNI *runtime*: it owns the container and hands its netns to a network plugin. How
the network is built is the plugin's; the agent knows it only through `AbstractCniPlugin`.

## The CNI contract (`cni.py`, `plugin/cni.py`)

| Verb | When the agent calls it | Plugin's promise |
|---|---|---|
| `add(CniRequest)` | the container is parked at its start gate, before its command runs | attach it; return its addresses and nameservers (`CniResult`) |
| `delete(CniRequest)` | `clean_kernel`, before the container is removed | give back what the ADD took; idempotent; ignore containers it never attached |
| `status()` | every heartbeat (`not_serving_reason`) | `not_ready_reason` set while it cannot serve an ADD |
| `gc(valid)` | agent start, after the container scan, before any lifecycle event | drop what it holds for containers not in `valid` |

- A session's network config names its plugin in `type` (`CNI_TYPE_KEY`). Loaded from entry point group `backendai_network_cni_v1`, and only when `agent.allow-cni-plugins` names its package path (`require_explicit_allow`): a loaded plugin gates the heartbeat, so an installed one that is not named is never called.
- `CniRequest.config` is opaque to the agent. `args` carry the session id, kernel id and cluster hostname; `runtime_config` carries port mappings and controller-assigned addresses.
- `netns` is always `/proc/<pid>/ns/net`; a DEL has none. A plugin may resolve the netns itself from the runtime rather than trust the path.
- DEL goes to every loaded plugin: the agent keeps no record of which one attached a container.
- GC runs before the queued START/CLEAN events: a CLEAN is a DEL, and the plugin must know the container by then.
- `init` gets `CniHostContext` (agent id, boot id, runtime backend, etcd, upstream nameservers). Node-local settings come from `[cni.<plugin>]` in the agent config, which the agent never reads.
- The agent publishes its boot id, then its runtime backend (`advert.py`), before any plugin starts: a plugin's adverts are fenced on that boot id.

## Two-phase start gate (`gate.py`, `docker/gate.py`)

- Docker execs the command at start (`docker create` gives no PID or netns), so a CNI-attached container starts behind a gate: the wrapper writes `ready`, blocks on the `go` FIFO, then execs in place, so the attached PID is the user's PID.
- `apply_gate` keeps the image entrypoint after the wrapper: replacing it dropped `/opt/kernel/entrypoint.sh` and the runner ran as root. The wrapper follows whichever of `EntryPoint` (the Docker backend) or `Entrypoint` (the API) is present.
- `signal_go` is non-blocking: a blocking FIFO open in an executor thread parks forever when the container never reached the gate.
- `wait_ready` waits for the marker, never a transient setup PID; `failure` is polled so an immediate death reports as broken, not slow.
- The gate is released whether the ADD succeeds or not: a container parked forever has no timeout and no message.

## Docker on a CNI network (`docker/agent.py`)

- A session whose network config has a `type` runs `NetworkMode: none` and is ADDed by that plugin; a plugin this agent has not loaded fails the create with `CniPluginNotInstalled`. A config without `type` is Docker's own, unchanged.
- `args` carry the session id, kernel id and cluster hostname; `runtime_config` carries the service `port_mappings` and the controller-assigned `ips` (`kernel_config["cluster_network_ip"]`).
- The container gets a bind-mounted `resolv.conf`, rewritten after the ADD to put the result's nameservers first.
- The REPL ports are dialled at the result's first IP (`repl_host`, kept in the recovery record), never forwarded; only service ports go into `port_mappings`. An ADD with no IP fails the create.
- Docker reports no ports for a `none` container, so on a CNI container the reserved ones ride the `ai.backend.internal.published-ports` label; `container_from_docker_container` reads it when Docker reports none, which keeps the port pool right across restarts.
- The ADD runs in `_provision_started_container`, so a failed attach is a failed create with a container to destroy.

## Withholding the heartbeat

- The manager marks a node ALIVE on a heartbeat alone, so while `not_serving_reason` gives a reason the heartbeat is withheld and `AgentTerminatedEvent(reason="agent-restart")` is sent once; the manager holds the node in RESTARTING, out of scheduling. The next heartbeat after recovery makes it ALIVE again.
- A plugin whose `status()` raises, or does not answer within `CNI_STATUS_TIMEOUT` (5s), is a reason too: a hung plugin must not hold the heartbeat.
- `_announcing` turns off only once the restarting event is sent; a failed send is retried on the next tick.

## Container nameservers (`dns.py`)

- `resolve_container_dns` drops loopback nameservers (the systemd-resolved stub is unreachable from the netns), falls back to the uplink file then 8.8.8.8, and forces `ndots:0`.
- `container.dns` pins the upstream nameservers. `CniHostContext.upstream_nameservers` re-reads them on each call.

## Container locator (`locator.py`)

A network plugin may run a privileged helper (root, separate process) that acts on container
network namespaces. The agent asks it to; `ContainerLocator` is how the helper checks the request
against the runtime instead of trusting it.

| Member | Answers | Why the helper needs it |
|---|---|---|
| `open` / `close` | Connect to / release the runtime | `open` runs before the helper serves, so an unreachable runtime fails at startup |
| `container_pid` | PID 1 of a running container, or `None` | The netns comes from this PID, not from the request; re-read after pinning to close the PID-reuse window |
| `live_sessions` | `{container_id: LiveContainer}` from one snapshot | Rebuilds the helper's state after a restart; containers whose `owner_agent_id` is another agent's are not reclaimed |
| `rootless` | Whether container records are written by the agent's non-root user | Default `False` |
| `cgroup_path` | Where a container's cgroup lives | Default refuses: the helper writes there as root, so a wrong answer is worse than none |

- Labels: `ai.backend.session-id` (every backend with a locator sets it) and `ai.backend.owner` (the placing agent; a node can run more than one).

### Construction

- `AbstractAgentDiscovery.create_container_locator` has no default: a guessed locator would answer "no such container" for every kernel.
- `build_container_locator(agent_config)` validates the agent config and asks that backend's discovery, so a helper does not import the agent's config schema or backend list. A config naming no backend fails validation.

### Docker (`docker/locator.py`)

- `cgroup_path` is unimplemented: the daemon places its own cgroups.
- `open` swaps in a new client only after `version()` succeeds, then closes the previous one; a failed re-open keeps the client that was answering.
- Using it before `open` raises `ContainerSourceUnwired`: an unconnected locator would read the node as empty.
- `container_pid` answers `None` only for a container the daemon reports as missing (404); any other daemon error is raised, so an unreachable daemon never reads as a stopped container.
- `live_sessions` reads labels from `containers.list`, one API call with no inspect per container.
