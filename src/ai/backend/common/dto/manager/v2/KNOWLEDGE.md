---
name: dto-v2-compat-policy
type: design-rationale
description: why the shared v2 DTO schema is additive-only (GQL and REST break together, version-branch schema policy), why clearable fields use the SENTINEL pattern, the current limitation of expressing nullify
scope: src/ai/backend/common/dto/manager/v2
keywords: [SSOT, additive-only, SENTINEL, nullify, BaseRequestModel, BaseResponseModel, supergraph, schema-inspector]
sources:
  - src/ai/backend/common/dto/manager/v2
  - scripts/generate-graphql-schema.sh
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# DTO v2 — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It is the single wire schema for every v2 operation — GraphQL types, REST v2
handlers, and the client SDK all derive from here. It exists to make the place
where a field is defined exactly one, so the surfaces cannot diverge.

## The schema is additive-only

- This schema serves the WebUI (GQL) and the CLI (REST) simultaneously — no surface can absorb a breaking change alone.
- The release version branches enforce the additive-only policy.
- The schema inspector sees v2 types only through the composed supergraph — name/type changes surface late and expensively.
- Add fields and deprecate old ones — do not change a field's name or purpose.

## Clearable fields use SENTINEL

- Update inputs already use `None` as "no change" (all optional fields default to `None`).
- So "clear it" needs a separate sentinel value — absent/None = keep, sentinel = clear, value = set.
- Collapsing onto `None` alone makes clearing impossible without per-field flags.

## Current limitation — expressing nullify

- The current DTOs cannot properly express "clear a field (nullify)" — there are cases that break at pydantic model creation time.
- This will be improved with the SENTINEL approach; until then, adding a clearable field means checking this limitation first.
