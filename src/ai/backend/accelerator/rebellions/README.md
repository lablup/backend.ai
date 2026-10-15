# Backend.AI Accelerator Plugin for Rebellions ATOM

## Installation
1. Copy `rbln-smi` binary to local agent directory and apply setuid bit on behalf of root account by running `sudo chmod u+s ./rbln-smi`
2. Create `atom.toml` configuration file where `[general].rbln_stat_path` is set to the absolute path of binary copied at step 1

## REBEL (Rebel100)
The `rebel100` plugin (slot `rebel100.device`, whole cards only) reads `rebel100.toml` (see `rebel100.toml.example`) instead of `atom.toml`.
It looks for `rbln-smi`, then `rbln-stat`, in `PATH` unless `[general].rbln_stat_path` is set.
Device names, CDI id and the device-id env var are pending the Rebel100 node and configurable.
Before starting the agent, register the `rebel100.device` slot type (no migration inserts it, and `agent_resources.slot_name` references `resource_slot_types`): create it with the v2 resource-slot slot-type create command as superadmin, or load `fixtures/manager/example-resource-slot-types.json` on a dev setup.
