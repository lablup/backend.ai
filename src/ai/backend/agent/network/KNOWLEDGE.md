---
name: agent-container-locator
type: design-rationale
description: The container locator — what a network plugin's privileged helper may see of an agent backend's containers, and why it reads them from the runtime rather than from the agent's request
scope: src/ai/backend/agent/network
keywords: [ContainerLocator, LiveContainer, DockerContainerLocator, DummyContainerLocator, build_container_locator, create_container_locator, ContainerSourceUnwired]
sources:
  - src/ai/backend/agent/network/locator.py
  - src/ai/backend/agent/network/locator_builder.py
  - src/ai/backend/agent/docker/locator.py
  - src/ai/backend/agent/dummy/locator.py
  - src/ai/backend/agent/types.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-09
status: stable
---

# Container locator — Knowledge

A network plugin may run a privileged helper (root, separate process) that acts on container
network namespaces. The agent asks it to; `ContainerLocator` is how the helper checks the request
against the runtime instead of trusting it.

## The helper acts only on what the runtime reports, never on the agent's request (`locator.py`)

| Member | Answers | Why the helper needs it |
|---|---|---|
| `open` / `close` | Connect to / release the runtime | `open` runs before the helper serves, so an unreachable runtime fails at startup |
| `container_pid` | PID 1 of a running container, or `None` | The netns comes from this PID, not from the request; re-read after pinning to close the PID-reuse window |
| `live_sessions` | `{container_id: LiveContainer}` from one snapshot | Rebuilds the helper's state after a restart; containers whose `owner_agent_id` is another agent's are not reclaimed |
| `rootless` | Whether container records are written by the agent's non-root user | Default `False` |
| `cgroup_path` | Where a container's cgroup lives | Default refuses: the helper writes there as root, so a wrong answer is worse than none |

- Labels: `ai.backend.session-id` (every backend with a locator sets it) and `ai.backend.owner` (the placing agent; a node can run more than one).

## A backend without its own locator has none; a locator is never guessed

- `AbstractAgentDiscovery.create_container_locator` has no default: a guessed locator would answer "no such container" for every kernel.
- Dummy (`dummy/locator.py`) reports no running containers, which is true of a backend that creates none. Kubernetes has no locator.
- `build_container_locator(agent_config)` validates the agent config and asks that backend's discovery, so a helper does not import the agent's config schema or backend list. A config naming no backend fails validation.

## The Docker locator never reads a daemon failure as an absent container (`docker/locator.py`)

- `cgroup_path` is unimplemented: the daemon places its own cgroups.
- `open` swaps in a new client only after `version()` succeeds, then closes the previous one; a failed re-open keeps the client that was answering.
- Using it before `open` raises `ContainerSourceUnwired`: an unconnected locator would read the node as empty.
- `container_pid` answers `None` only for a container the daemon reports as missing (404); any other daemon error is raised, so an unreachable daemon never reads as a stopped container.
- `live_sessions` reads labels from `containers.list`, one API call with no inspect per container.
