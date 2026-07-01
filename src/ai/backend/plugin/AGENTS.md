# Plugin Loading

This package is the **entry-point scanner / CLI** (`entrypoint.py`, `cli.py`). Plugin base classes and the loader context live in `ai.backend.common.plugin` — write new plugins against those.

## How plugins load

- Discovered via Python entry points, group `backendai_{domain}_v{N}` (e.g. `backendai_hook_v20`, `backendai_accelerator_v21`, `backendai_webapp_v20`).
- `scan_entrypoints(group)` chains three sources: Pants BUILD files, plugin checkouts, installed package metadata.
- Inspect with `./bai plugin scan <group>`.

## Write / register a plugin

- Subclass `AbstractPlugin` (`common/plugin/__init__.py`) — implement async `init()`, `cleanup()`, `update_plugin_config()` — or a typed interface (`HookPlugin`, `AbstractEventDispatcherPlugin`, `WebappPlugin`, `AbstractComputePlugin`, monitor plugins).
- Register by declaring `entry_points` under the right group in the distribution's BUILD file.

## Pitfalls

- Duplicate plugin name across sources raises at load; a name in both allowlist and blocklist is a `ConfigurationError`.
- A class not inheriting `AbstractPlugin` is skipped with a warning.
- Plugin etcd config path is `config/plugins/{group_key}/{plugin_name}/`.
