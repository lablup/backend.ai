<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Migration strategy and backward compatibility guarantees
depends-on: [kata-agent-backend.md, vfio-accelerator-plugin.md, scheduler-integration.md, configuration-deployment.md]
key-decisions:
  - All changes are additive; no existing behavior modified
  - Kata agents deployed alongside Docker agents in separate scaling groups
  - Rollback is trivial (remove Kata agents, keep schema)
-->

# BEP-1049: Migration and Compatibility

## Summary

Introducing KataAgent is an additive change — new enum value, new package, new config section, new DB column with a safe default. Existing Docker and Kubernetes deployments are completely unaffected. This document details the rollout strategy, compatibility guarantees, and rollback plan.

## Backward Compatibility

### No Breaking Changes

| Component | Change | Impact on Existing Deployments |
|-----------|--------|-------------------------------|
| `AgentBackend` enum | Add `KATA = "kata"` | None — existing `DOCKER`/`KUBERNETES` values unchanged |
| `AgentRow` | Add `backend` column | None — `server_default="docker"` for all existing rows |
| Agent heartbeat | Add `backend` field | None — manager defaults to `"docker"` if field missing |
| Accelerator plugins | New `cuda_vfio` entry point | None — only loaded if agent config allows it |
| Scaling groups | No schema change | None — new groups created for Kata, existing groups unchanged |
| Manager RPC | No protocol change | None — `create_kernel` payload is identical |
| User API | No change | None — users select scaling groups, not backends |
| `AgentMeta` / `AgentInfo` | Add `backend` field with default | None — default `"docker"` preserves behavior |

### Package Independence

The `ai.backend.agent.kata` package is a new addition:

```
src/ai/backend/agent/
├── docker/          ← unchanged
├── kubernetes/      ← unchanged
├── dummy/           ← unchanged
└── kata/            ← new (only imported when backend="kata")
```

The `ai.backend.accelerator.cuda_vfio` package is similarly independent:

```
src/ai/backend/accelerator/
├── cuda_open/       ← unchanged (Docker agents continue using this)
└── cuda_vfio/       ← new (only loaded by Kata agents)
```

### Config Compatibility

The `[kata]` config section is only read when `[agent] backend = "kata"`. Docker agents ignore it entirely. Existing `agent.toml` files require no changes.

## Migration Steps

### Phase 1: Infrastructure Preparation

Before deploying any Backend.AI changes:

1. **Prepare Kata hosts** (dedicated machines or a subset of existing agent nodes):
   - Install Kata Containers 3.x (`kata-runtime`, guest kernel, rootfs image)
   - Configure containerd with Kata shim (`io.containerd.kata.v2`)
   - Enable IOMMU in kernel: `intel_iommu=on iommu=pt` (Intel) or `amd_iommu=on iommu=pt` (AMD)
   - Load kernel modules: `vfio`, `vfio_pci`, `vfio_iommu_type1`, `vhost_vsock`
   - Bind target GPUs to `vfio-pci` driver
   - Verify: `kata-runtime check` passes, `/dev/vfio/` contains group devices

2. **Verify IOMMU groups** on each host:
   ```bash
   for d in /sys/kernel/iommu_groups/*/devices/*; do
     echo "IOMMU Group $(basename $(dirname $(dirname $d))):" \
       "$(lspci -nns $(basename $d))"
   done
   ```
   Confirm each GPU is in its own IOMMU group (or shares only with its audio companion).

### Phase 2: Backend.AI Deployment

1. **Run Alembic migration**:
   - Adds `agents.backend` column with `server_default="docker"`
   - Non-destructive; can be run while existing agents are online
   - Existing agent rows automatically get `backend="docker"`

2. **Deploy updated manager**:
   - Manager accepts the new `backend` field in agent heartbeats
   - Falls back to `"docker"` for agents that don't send it (backward compatible)

3. **Create Kata scaling group(s)**:
   ```sql
   INSERT INTO scaling_groups (name, driver, ...) VALUES ('kata-gpu', 'static', ...);
   ```
   Or via admin API / WebUI.

4. **Deploy Kata agent on prepared hosts**:
   - Config file with `[agent] backend = "kata"` and `[kata]` section
   - Agent registers with the Kata scaling group
   - Agent heartbeat includes `backend="kata"`

### Phase 3: Validation

1. **Agent registration**: Verify Kata agents appear in `agents` table with `backend="kata"`:
   ```sql
   SELECT id, backend, scaling_group, available_slots FROM agents WHERE backend = 'kata';
   ```

2. **Session creation**: Create a test session targeting the Kata scaling group:
   - CPU-only session first (Phase 1 validation)
   - Single GPU session (Phase 2 validation)
   - Multi-GPU session (if IOMMU groups allow)

3. **GPU verification**: Inside the Kata session:
   ```bash
   nvidia-smi  # Should show passthrough GPU(s)
   python -c "import torch; print(torch.cuda.device_count())"
   ```

4. **Storage verification**: Confirm vfolder mounts are accessible:
   ```bash
   ls /home/work/  # Should show mounted vfolders
   echo "test" > /home/work/test.txt  # Write should succeed
   ```

5. **Existing Docker sessions**: Verify no impact:
   - Create sessions in Docker scaling groups — should work identically
   - Check Docker agent heartbeats — `backend="docker"` (or missing, defaulted)
   - Confirm no scheduler behavior changes for Docker groups

### Phase 4: Gradual Rollout

1. **Start small**: One Kata agent, one scaling group, internal testing only
2. **Assign specific projects/users** to the Kata scaling group for controlled testing
3. **Monitor**:
   - VM boot times (target: < 500ms)
   - Memory overhead (should match `kata.vm-overhead-mb` config)
   - GPU compute performance (should be near-native via VFIO)
   - I/O performance on vfolder mounts (virtio-fs overhead)
4. **Scale out**: Add more Kata agents as confidence grows

## Rollback Plan

Rollback is straightforward because all changes are additive:

1. **Remove Kata agents** from the Kata scaling group (or set `schedulable=false`)
2. **Reassign users/projects** back to Docker scaling groups
3. **Optionally remove Kata agents** from the cluster entirely
4. **No schema rollback needed**: The `agents.backend` column stays (all values are `"docker"` after Kata agents are removed); the Alembic migration does not need to be reversed

The `backend` column, `AgentBackend.KATA` enum value, and `cuda_vfio` plugin are inert when no Kata agents are deployed — they add no runtime overhead or behavioral changes.

## Future Extensibility

### Phase 4: Confidential Computing

When implementing CoCo (Confidential Containers) support:

- Add `confidential_guest = true` and `guest_attestation = "tdx"` to Kata config
- Guest image pull: images downloaded and decrypted inside the TEE
- Key Broker Service (KBS) integration for sealed secrets
- Remote attestation endpoint exposed via the manager API
- Dedicated scaling group: `kata-confidential` with CoCo-enabled agents
- No changes to the scheduler or resource accounting model

### BEP-1016 Alignment

When Accelerator Interface v2 (BEP-1016) is implemented:

- Migrate `CUDAVFIOPlugin.generate_docker_args()` → `create_lifecycle_hook()`
- The `WorkloadConfig` struct replaces the `_kata_vfio_devices` convention:
  ```python
  class WorkloadConfig:
      mounts: list[MountInfo]
      env_vars: dict[str, str]
      resource_data: dict[str, str]
      # VFIO devices expressed as mounts or a dedicated field
  ```
- Both `CUDAPlugin` and `CUDAVFIOPlugin` implement the same interface
- No user-facing or scheduler changes needed

### Mixed Scaling Groups (Future Option)

If operational needs require mixed Docker/Kata agents in the same scaling group:

- Add `allowed_backends: list[str]` to `ScalingGroupOpts`
- Add backend filtering to `AgentSelector`:
  ```python
  candidates = [a for a in agents if a.backend in sgroup.allowed_backends]
  ```
- Add `preferred_backend` to `SessionCreationSpec` (optional, user-specified)
- This is NOT proposed for the initial implementation — homogeneous groups are simpler and sufficient

## References

- [Configuration & Deployment](configuration-deployment.md) — host requirements checklist
- [Scheduler Integration](scheduler-integration.md) — `AgentRow.backend` column details
- [Kata Containers Installation Guide](https://github.com/kata-containers/kata-containers/blob/main/docs/install/README.md)
