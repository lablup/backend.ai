<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Manager and scheduler changes for Kata backend selection and resource accounting
depends-on: [kata-agent-backend.md, vfio-accelerator-plugin.md]
key-decisions:
  - Backend selection via homogeneous scaling groups
  - VM overhead deducted from agent available_slots at registration
  - backend column added to AgentRow (default "docker")
-->

# BEP-1049: Scheduler Integration

## Summary

Manager and scheduler changes to track agent backend types, route sessions to Kata agents via scaling group assignment, and account for per-VM memory overhead in resource scheduling. All changes are additive — existing Docker scheduling behavior is unchanged.

## Current Design

### Agent Registration

Agents register via heartbeat events. The manager creates/updates `AgentRow` (`src/ai/backend/manager/models/agent/row.py:62`):

```python
class AgentRow(Base):
    id: Mapped[str]                    # Agent ID
    status: Mapped[AgentStatus]
    region: Mapped[str]
    scaling_group: Mapped[str]         # FK to scaling_groups.name
    available_slots: Mapped[ResourceSlot]   # Total capacity
    occupied_slots: Mapped[ResourceSlot]    # Currently used
    architecture: Mapped[str]          # e.g., "x86_64"
    compute_plugins: Mapped[dict]      # Loaded plugin metadata
    # No backend type field exists
```

### Agent Selection

The scheduler selects agents via `AgentSelector` implementations. `AgentInfo` (`src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py`) contains:

```python
@dataclass
class AgentInfo:
    id: AgentId
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    architecture: str
    # No backend type field
```

The selector filters by `available_slots >= requested_slots` within the target scaling group.

### Scaling Groups

`ScalingGroupOpts` (`src/ai/backend/manager/models/scaling_group/row.py`) configures:

```python
class ScalingGroupOpts:
    allowed_session_types: list[SessionTypes]
    agent_selection_strategy: AgentSelectionStrategy  # DISPERSED, CONCENTRATED, etc.
    # No backend preference
```

Sessions are assigned to a scaling group; the scheduler then picks an agent within that group.

## Proposed Design

### Agent Backend Tracking

Add a `backend` column to `AgentRow`:

```python
class AgentRow(Base):
    # ... existing columns ...
    backend: Mapped[str] = mapped_column(
        "backend",
        sa.String(length=16),
        nullable=False,
        server_default="docker",
        default="docker",
    )
```

**Alembic migration:**

```python
def upgrade():
    op.add_column(
        "agents",
        sa.Column(
            "backend",
            sa.String(length=16),
            nullable=False,
            server_default="docker",
        ),
    )
```

This is non-destructive: all existing agents get `backend="docker"` via the server default.

### Agent Heartbeat Extension

The agent heartbeat payload already includes metadata (architecture, version, compute_plugins). Add `backend`:

```python
# In agent heartbeat handler (manager side)
async def handle_agent_heartbeat(self, agent_id, heartbeat_data):
    backend = heartbeat_data.get("backend", "docker")  # backward-compatible default
    await self._update_agent_row(agent_id, backend=backend, ...)
```

On the agent side, the heartbeat includes `AgentBackend.value`:

```python
# In AbstractAgent heartbeat sender
heartbeat_data = {
    "backend": self.local_config.agent_common.backend.value,
    "architecture": platform.machine(),
    # ... existing fields ...
}
```

### Homogeneous Scaling Groups

The recommended approach: each scaling group contains agents of a single backend type. No new columns on `ScalingGroupRow`.

**Why homogeneous:**

1. **Simplicity**: The existing scheduling flow is unchanged — sessions target a scaling group, the scheduler picks an agent within it. Backend type is implicit from the group.
2. **Operational clarity**: Operators know exactly which groups run Kata and which run Docker.
3. **No agent filtering changes**: The `AgentSelector` does not need backend-aware filtering.
4. **Resource semantics match**: `cuda.device` means the same thing in both backends (1 whole GPU), but the attachment mechanism differs. Keeping backends in separate groups prevents accidental mixing.

**Deployment example:**

```
Scaling Groups:
├── default          → DockerAgent instances (general compute)
├── gpu-docker       → DockerAgent instances with GPUs (NVIDIA runtime)
├── gpu-kata         → KataAgent instances with GPUs (VFIO passthrough)
└── kata-confidential → KataAgent instances with CoCo enabled
```

Users/projects are assigned to scaling groups as before; selecting `gpu-kata` routes the session to a Kata agent.

### VM Memory Overhead Accounting

Each Kata VM consumes host memory for the hypervisor process, guest kernel, and kata-agent. This overhead must be reflected in schedulable resources.

**Approach: Agent-side deduction**

The Kata agent deducts VM overhead from `available_slots.mem` at registration:

```python
# In KataAgent.scan_available_resources()
async def scan_available_resources(self, compute_device_types):
    base_slots = await super().scan_available_resources(compute_device_types)

    kata_config = self.local_config.kata
    # Reserve memory for max concurrent VMs
    # Each session = 1 VM, so max_sessions * overhead
    max_concurrent = self._estimate_max_concurrent_sessions(base_slots)
    overhead_bytes = max_concurrent * kata_config.vm_overhead_mb * 1024 * 1024

    adjusted_mem = base_slots.get(SlotName("mem"), Decimal(0)) - Decimal(overhead_bytes)
    if adjusted_mem < 0:
        adjusted_mem = Decimal(0)

    result = dict(base_slots)
    result[SlotName("mem")] = adjusted_mem
    return result
```

**Why agent-side deduction:**

1. The scheduler sees accurate `available_slots` — no special-case logic needed
2. VM overhead is a property of the agent's configuration, not the session
3. The overhead amount is configurable via `kata.vm-overhead-mb`
4. No changes to `ResourceSlot` semantics visible to users or the API

### Resource Slot Compatibility

| Slot Name | Docker (CUDAPlugin) | Kata (CUDAVFIOPlugin) | Scheduler View |
|-----------|---------------------|------------------------|----------------|
| `cpu` | cgroup CPU shares | VM vCPU allocation | Identical |
| `mem` | cgroup memory limit | VM memory (minus overhead) | Identical |
| `cuda.device` | NVIDIA Container Toolkit | VFIO passthrough | Identical |
| `cuda.shares` | Fractional (hook libraries) | **Not available** | N/A for Kata agents |

The scheduler treats `cuda.device` identically regardless of backend. The CUDAVFIOPlugin does not define `cuda.shares`, so it simply does not appear in Kata agents' `available_slots`.

### AgentMeta / AgentInfo Updates

Add `backend` to data transfer objects used by the scheduler:

```python
# src/ai/backend/manager/repositories/scheduler/types/agent.py
@dataclass
class AgentMeta:
    id: AgentId
    addr: str
    architecture: str
    available_slots: ResourceSlot
    scaling_group: str
    backend: str = "docker"  # NEW, backward-compatible default

# src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py
@dataclass
class AgentInfo:
    id: AgentId
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot
    architecture: str
    backend: str = "docker"  # NEW
```

These fields are informational in the homogeneous scaling group model — the selector does not need to filter by backend. They are useful for:
- Admin visibility (GQL queries: "show me all Kata agents")
- Future mixed-group support (if ever needed)
- Monitoring and dashboards

### GraphQL Exposure

Add `backend` to the `Agent` GQL type:

```python
@strawberry.type
class AgentNode:
    # ... existing fields ...
    backend: str  # "docker" | "kubernetes" | "kata"
```

This lets the admin UI display which agents use which backend.

## Interface / API

| Change | Location | Type |
|--------|----------|------|
| `AgentRow.backend` column | `src/ai/backend/manager/models/agent/row.py` | DB schema (Alembic) |
| `AgentMeta.backend` field | `src/ai/backend/manager/repositories/scheduler/types/agent.py` | Dataclass |
| `AgentInfo.backend` field | `src/ai/backend/manager/sokovan/scheduler/provisioner/selectors/selector.py` | Dataclass |
| Heartbeat `backend` field | Agent heartbeat sender + Manager heartbeat handler | Protocol |
| `AgentNode.backend` | GQL Agent type | API |

## Implementation Notes

- The Alembic migration is non-destructive: adds a column with `server_default="docker"`
- Agent heartbeat backward compatibility: if `backend` is missing from heartbeat, default to `"docker"`
- No changes to the RPC protocol between Manager and Agent for `create_kernel` / `destroy_kernel` — the payload is the same; only the agent-side handling differs
- The `compute_plugins` JSONB column on `AgentRow` already captures which plugins are loaded (e.g., `cuda` vs `cuda_vfio`), providing implicit backend information. The explicit `backend` column adds clarity.
