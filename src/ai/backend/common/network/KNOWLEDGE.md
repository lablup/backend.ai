---
name: common-network-shared-keys
type: design-rationale
description: The etcd keys core shares between agent and manager about cluster networking, whichever network plugin runs — the agent boot and backend keys and why the boot key goes first
scope: src/ai/backend/common/network
keywords: [agent_boot_key, agent_backend_key, publish_backend]
sources:
  - src/ai/backend/common/network/keys.py
  - src/ai/backend/agent/network/advert.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-09
status: stable
---

# Core networking keys — Knowledge

A network plugin keeps its own keys under `network/`; these are the ones core writes or reads.

| Key | Writer | Reader |
|---|---|---|
| `network/agent/{id}/boot` | agent at every start, first | anyone fencing an advert on the current run |
| `network/agent/{id}/backend` | agent at every start, after `boot` | the manager's driver/backend pairing |

- The boot id goes first: with the backend first, a same-runtime restart briefly re-admits whatever the previous run advertised.
- Both are written before any network plugin starts, so a plugin can fence its own adverts on the boot id.
