---
name: agent-node-authority
type: design-rationale
description: The agent as the component that actually creates/manages kernels, node authority and the RPC-in/event-out asymmetry, three coexisting RPC generations, multi-agent hosting in a single process, kernel-registry persistence and recovery, the privileged watcher process
scope: src/ai/backend/agent
keywords: [AbstractAgent, AgentRuntime, kernel_registry, heartbeat, RPC, watcher, recovery, Callosum]
sources:
  - src/ai/backend/agent/runtime.py
  - src/ai/backend/agent/rpc
  - src/ai/backend/agent/kernel_registry
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Agent — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this component exists

The agent is **the component that actually creates and manages kernels
(containers)**. Turning the sessions the manager decided on into running state
on a node and keeping them there — creation/destruction, node resource
allocation, status collection/reporting — all happens here.

## The node is the authority

- The agent owns what is actually running on the node — the manager's DB is a projection of what the agent reported.
- Communication is deliberately asymmetric: manager→agent is ZeroMQ RPC, agent→manager is events plus periodic heartbeats.
- The heartbeat payload carries the full image list and resource slots — extending `AgentInfo` is a manager-compatibility concern.

## Three generations of RPC coexist

- The v1/v2 class-level registries are still bound at startup.
- New handlers go into the injectable v3 registry (`rpc/routing.py`).
- v3 dispatch determines the target agent from the `agent_id` in the call envelope.

## One process can host multiple agents

- `AgentRuntime` maps `AgentId → AbstractAgent` with a shared kernel registry and resource allocator.
- Do not assume a module- or process-level singleton belongs to a specific agent.

## State must survive restarts

- The kernel registry is persisted via pickle snapshots plus container-label mirroring and recovered at boot (`kernel_registry/recovery/`).
- Any new field that must survive restarts has to be added to the recovery data, not just the in-memory object.

## The watcher is a separate privileged process

- It is its own aiohttp process and can start/stop/reset the agent — do not assume the agent owns its own restart.
- The auth token (etcd `config/watcher/token`) defaults to the literal `"insecure"` — it must be configured in deployments.
- Do not fold the watcher's duties into the agent server.
- This structure is not an agent-specific end state — **the plan is to generalize it so every server can be run the same way (a watcher managing the server process)**.
