# Config samples: Guardrails

## `sample.toml` is generated: do not edit directly

Each component's `sample.toml`, such as `configs/webserver/sample.toml`, is a view generated from the config schema, not a hand-maintained file. The block and field comments, defaults and example values all come from each field's `BackendAIConfigMeta` annotation in that component's `config/unified.py`.

Do not edit `sample.toml` directly: it is overwritten on regeneration and drifts from the schema (the source of truth).

To make changes:
1. Edit the field's `description=`, defaults and examples in the component's `config/unified.py`.
2. Regenerate with the component's `generate-sample` CLI in `src/ai/backend/{component}/cli/config.py`.
   See `./backend.ai web generate-sample --overwrite` for the web server.

The legacy `.conf` samples are hand-maintained with actual local example values and are separate from the generated `.toml`; see `configs/webserver/sample.conf`.
