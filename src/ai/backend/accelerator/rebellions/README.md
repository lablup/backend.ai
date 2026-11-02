# Backend.AI Accelerator Plugin for Rebellions ATOM and REBEL

## Installation
1. Copy `rbln-smi` binary to local agent directory and apply setuid bit on behalf of root account by running `sudo chmod u+s ./rbln-smi`
2. Create `atom.toml` configuration file where `[general].rbln_stat_path` is set to the absolute path of binary copied at step 1

## REBEL (Rebel100)
The `rebel100` plugin (slot `rebel100.device`, whole cards only, device name `RBLN-CR13`) reads `rebel100.toml` instead of `atom.toml`, searched in the working directory, `~/.config/backend.ai/` and `/etc/backend.ai/` (see `rebel100.toml.example`).
Set `[general].rbln_stat_path` to the absolute path of `rbln-smi`.
RSD groups are always off (`enable_rsd` is ignored): CDI always injects `/dev/rsd0` (group 0), so a card moved to another group is invisible to the SDK in the container.
Only the assigned cards are requested through CDI (`rebellions.ai/npu=<N>`, `N` from the host `/dev/rbln<N>`).
Agent config:
- `[agent] allow-compute-plugins` must include `"ai.backend.accelerator.rebellions.rebel100"`.
- `[resource] allocation-order` must include `"rebel100"`, otherwise kernel creation fails with `ValueError: 'rebel100' is not in list`.
The `rebel100.device` slot type, which `agent_resources.slot_name` references, comes from `seeds/manager/resource_slot_type/defaults.yaml` on a fresh install and from a manager migration on an upgrade.

## Operational notes
- The runner waits 30 s for a service port to open, while vLLM loads for minutes: use the model-service path, or a wrapper that opens the port early.
- Containers run with `IpcMode: host`, so `psm_*`, `sem.mp-*` and SysV segments (mode 666) left by vLLM and `rbln-ccl` stay in the host IPC namespace; clean them up periodically.
- The Rebel100 runtime and `rbln-ccl` also work with private IPC, but multi-process vLLM (TP/PP) then needs `/dev/shm` of at least 160 MiB (session `shmem`); the 64 MiB default fails.
