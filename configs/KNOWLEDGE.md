---
name: configs-generated-vs-hand
type: reference
description: the dual configuration sources (TOML files and etcd) and their division of roles, the four kinds of files under configs (only sample.toml is generated), the checklist for adding a config key, load order and hot reload
scope: configs
keywords: [sample.toml, halfstack.toml, BackendAIConfigMeta, generate-sample, etcd, unified.py, added_version]
sources:
  - src/ai/backend/common/meta/meta.py
  - src/ai/backend/manager/config
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# configs/ — Knowledge

> Rules: `AGENTS.md` in the same directory (sample.toml is a generated file — do not edit directly).

## Why this directory exists

It gathers each component's configuration schema view and local development
templates. This document holds the background on why configuration is read from
two sources — files and etcd — and what to update when adding a key.

## There are two configuration sources — files and etcd

| Source | Holds | Change propagation |
|---|---|---|
| TOML file (per component) | Node/process-local settings | Read only at boot — restart required |
| etcd | Cluster-global settings (shared resources, volumes, redis connection, etc.) | Watched; on change the whole config is re-validated (hot reload) |

- Both sources merge into one pydantic unified config (`config/unified.py`) — what code reads is always the unified config.
- Deciding where a key belongs: file if it differs per node, etcd if the cluster shares it.

## Four kinds of files, only one generated

| Kind | Examples | Maintenance |
|---|---|---|
| Generated schema view | `{component}/sample.toml` | Regenerated via `generate-sample` |
| Local development templates | `halfstack.toml`, `ci.toml`, `halfstack.alembic.ini`, `sample.conf` | Manual |
| etcd seed JSON | `manager/sample.etcd.*.json` | Manual |
| Third-party infrastructure | prometheus, loki, tempo, grafana, traefik, systemd, graphql | Manual |

- There is no CI check that regenerates/diffs `sample.toml` — drift is caught only in review.

## Load order

1. TOML file
2. Environment variable overrides — **beat the file**
3. Explicit overrides
4. Validation via the pydantic unified config (TOML is kebab-case, Python is snake_case)

## Checklist for adding a config key

1. Add the field with `BackendAIConfigMeta` to the component's `config/unified.py` — `description` and `added_version` are required (the version becomes the `# Added in X.Y.Z` comment).
2. Regenerate: `./backend.ai {component} config generate-sample --overwrite`
3. If local development needs a value, update `halfstack.toml`/`ci.toml` manually — these are not generated.
4. For an etcd-based key, update the etcd tree docstring in `unified.py` and the corresponding `sample.etcd.*.json`.
