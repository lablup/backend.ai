# Accelerator Plugins

Hardware compute plugins (cuda_open, rocm, habana, furiosa, rebellions, …) loaded via entry-point group `backendai_accelerator_v21`. `mock/` is the test/dev simulator (config-driven, random stats).

## Add an accelerator

- Implement `AbstractComputePlugin` (`agent/resources.py`) and back each device with an `AbstractComputeDevice`. Key methods: `get_metadata()` / `get_version()` (sync); `list_devices()` / `available_slots()` / `create_alloc_map()` / `generate_docker_args()` (async). See `mock/plugin.py` for a complete reference.
- Layout: single-device accelerators use `plugin.py` + `types.py` + a driver module; multi-model families (habana, rebellions) put shared abstracts in `common/` and one subdir per model.
- Register the plugin class under `backendai_accelerator_v21` in the package BUILD file.

## Rules

- Slot names must start with the plugin key (`cuda.device`, not `device`); stat metric keys must be `{key}_*` to avoid collisions across plugins.
- Pick the alloc map by mode: `DiscretePropertyAllocMap` vs `FractionAllocMap`.
- `plugin_config` is dynamic (etcd, live); `local_config` is the daemon TOML (restart only) — don't confuse them.
