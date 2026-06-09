# Configuration Samples — Guidelines

## `sample.toml` files are generated, not hand-edited

Each component's `sample.toml` (e.g. `configs/webserver/sample.toml`) is a **generated
view** of its config schema, not a hand-maintained file. The block/field comments,
defaults, and example values all come from each field's `BackendAIConfigMeta` annotation
in that component's `config/unified.py`.

**Do NOT edit `sample.toml` directly** — changes are overwritten on regeneration and
diverge from the schema source of truth.

To change a `sample.toml`:
1. Edit the field's `description=` (and default/example) in the component's
   `config/unified.py`.
2. Regenerate via the component's `generate-sample` CLI command (implemented in
   `src/ai/backend/{component}/cli/config.py`), e.g. for the web server:
   `./backend.ai web generate-sample --overwrite`.

Note: the older `.conf` sample files (e.g. `configs/webserver/sample.conf`) are
hand-maintained with real local example values and are separate from the generated
`.toml` files.
