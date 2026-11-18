# Config samples: Guardrails

## `sample.toml.j2` is generated: do NOT edit directly

Each component's `sample.toml.j2`, such as `configs/webserver/sample.toml.j2`, is a Jinja template generated from the config schema, not a hand-maintained file. The block/field comments, defaults, and example values all come from each field's `BackendAIConfigMeta` annotation in that component's `config/unified.py`.

Do NOT edit `sample.toml.j2` directly: it is overwritten on regeneration and drifts from the schema (the source of truth).

To make changes:
1. Edit the field's `description=` (and defaults/examples) in the component's `config/unified.py`.
2. Regenerate with the component's `generate-sample` CLI (`src/ai/backend/{component}/cli/config.py`).
   Example: for the web server, `./backend.ai web config generate-sample --overwrite --unmask-secrets`.

## A DICT field of tables becomes a template argument

The entry key of a `composite=CompositeType.DICT` field whose entries are tables becomes a template argument named after the field key plus `_name` (`artifact-storages` → `{{ artifact_storages_name }}`). Renaming such a field renames the argument that `config render` takes. A DICT of plain values gets no argument.

A template is not a configuration: write one with `./backend.ai {component} config render -t <template> -a NAME=VALUE ... -o <output>`.

See: the legacy `.conf` samples (e.g., `configs/webserver/sample.conf`) are hand-maintained with actual local example values and are separate from the generated `.toml.j2`.
