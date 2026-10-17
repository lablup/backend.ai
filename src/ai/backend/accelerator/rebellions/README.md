# Backend.AI Accelerator Plugin for Rebellions ATOM

## Installation
1. Copy `rbln-smi` binary to local agent directory and apply setuid bit on behalf of root account by running `sudo chmod u+s ./rbln-smi`
2. Create `atom.toml` configuration file where `[general].rbln_stat_path` is set to the absolute path of binary copied at step 1

## REBEL (Rebel100)
The `rebel100` plugin (slot `rebel100.device`, whole cards only, device name `RBLN-CR13`) reads `rebel100.toml` instead of `atom.toml`, searched in the working directory, `~/.config/backend.ai/` and `/etc/backend.ai/` (see `rebel100.toml.example`).
It looks for `rbln-smi`, then `rbln-stat`, in `PATH` unless `[general].rbln_stat_path` is set; with RSD off (the default) the plain executable works without root or setuid.
Only the assigned cards are requested through CDI (`rebellions.ai/npu=<N>`, `N` from the host `/dev/rbln<N>`).
Agent config:
- `[agent] allow-compute-plugins` must include `"ai.backend.accelerator.rebellions.rebel100"`.
- `[resource] allocation-order` must include `"rebel100"`, otherwise kernel creation fails with `ValueError: 'rebel100' is not in list`.
Before starting the agent, register the `rebel100.device` slot type (no migration inserts it, and `agent_resources.slot_name` references `resource_slot_types`): create it with the v2 resource-slot slot-type create command as superadmin, or load `fixtures/manager/example-resource-slot-types.json` on a dev setup.
