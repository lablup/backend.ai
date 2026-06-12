# Config samples — Guardrails

## `sample.toml` is generated — do NOT edit directly

Each component's `sample.toml` (e.g., `configs/webserver/sample.toml`) is a view generated from the config schema, not a hand-maintained file. The block/field comments, defaults, and example values all come from each field's `BackendAIConfigMeta` annotation in that component's `config/unified.py`.

Do NOT edit `sample.toml` directly — it is overwritten on regeneration and drifts from the schema (the source of truth).

To make changes:
1. Edit the field's `description=` (and defaults/examples) in the component's `config/unified.py`.
2. Regenerate with the component's `generate-sample` CLI (`src/ai/backend/{component}/cli/config.py`).
   Example: for the web server, `./backend.ai web generate-sample --overwrite`.

See: the legacy `.conf` samples (e.g., `configs/webserver/sample.conf`) are hand-maintained with actual local example values and are separate from the generated `.toml`.
