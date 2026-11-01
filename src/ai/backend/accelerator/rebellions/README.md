# Backend.AI Accelerator Plugin for Rebellions ATOM

## Installation
1. Copy the `rbln-smi` binary to the local agent directory and set the setuid bit for the root account with `sudo chmod u+s ./rbln-smi`.
2. Create the `atom.toml` configuration file and set `[general].rbln_stat_path` to the absolute path of the binary copied in step 1.
