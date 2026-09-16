---
name: dto-v2-compat-policy
type: design-rationale
description: why the shared v2 DTO schema is additive-only (GQL and REST break together, version-branch schema policy), why update fields separate omitted from null with Unset
scope: src/ai/backend/common/dto/manager/v2
keywords: [SSOT, additive-only, Unset, UNSET, nullify, BaseRequestModel, BaseResponseModel, supergraph, schema-inspector]
sources:
  - src/ai/backend/common/dto/manager/v2
  - src/ai/backend/common/tristate/unset.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
updated:
  by: claude-code/fable-5
  at: 2026-09-08
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

## Update fields separate omitted from null with `Unset`

- An update field is `X | None | Unset = Field(default=UNSET)` — omitted = no change, null = clear, value = set.
- An omitted field puts nothing on the wire and nothing in the JSON schema.
- Which of null and unset a column honours is the adapter's decision; the rule table lives in the "Update" section of `../../AGENTS.md`, the sentinel's rationale in [`../../../tristate/KNOWLEDGE.md`](../../../tristate/KNOWLEDGE.md).
- Fields still declared with the legacy `Sentinel` enum are being migrated one domain at a time; do not add new ones.
