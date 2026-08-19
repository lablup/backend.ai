# BEP proposals — Guardrails

> Process, status lifecycle, and number registry: `README.md`.
> Full writing guide (structure, segmentation, context-for-ai): `/bep-guide` skill.

## Rules

- **A BEP is a tech spec, not an implementation log.** Describe interfaces, contracts, and design decisions — not line-by-line code.
- **Reserve a number first.** Add your entry to the BEP Number Registry in `README.md` before creating the document.
- **Reference, don't expand.** For an implementation-level BEP, link the upstream motivation/spec BEP; do not rewrite it.

## What goes in the BEP vs. the PR

The boundary is **"does this need a structural design decision?"** — internal-only structural decisions still belong in the BEP.

| In the BEP (tech spec) | In the PR (implementer's discretion) |
|------------------------|--------------------------------------|
| Component responsibilities & boundaries, layer placement | Exact dataclass fields / function signatures |
| Observable contracts: state transitions, API / config field *meaning* | File / function / line anchors |
| Design decisions and rationale (including internal ones) | Algorithm optimizations, data-structure choices |
| The core flow across layers | Marker / storage locations, wiring details |

Symbol/file references in the "current design" section are status evidence (reader pointers), not implementation detail — keep them minimal but allowed.

## Tech-spec BEP structure

Implementation-level BEPs use this structure (detail and example in `/bep-guide`):

`Goal → Current design & scope by area (✅ exists / ➕ to add) → Implementation design → Decision Summary → Open Questions → References`

The **by-area current-design table** (split by API / DB / Scheduler / …, each separating what exists from what is missing) is the distinguishing element. Reference example: `BEP-1055-preemption-scheduler-mechanics.md`.
