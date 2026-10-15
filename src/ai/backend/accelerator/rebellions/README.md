# Backend.AI Accelerator Plugin for Rebellions ATOM

## Installation
1. Copy `rbln-smi` binary to local agent directory and apply setuid bit on behalf of root account by running `sudo chmod u+s ./rbln-smi`
2. Create `atom.toml` configuration file where `[general].rbln_stat_path` is set to the absolute path of binary copied at step 1

## REBEL (Rebel100)
The `rebel` plugin (slot `rebel.device`, whole cards only) reads `rebel.toml` (see `rebel.toml.example`) instead of `atom.toml`.
It looks for `rbln-smi`, then `rbln-stat`, in `PATH` unless `[general].rbln_stat_path` is set.
Device names, CDI id and the device-id env var are pending the Rebel100 node and configurable.
