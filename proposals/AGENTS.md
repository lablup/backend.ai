# BEP proposals: Guardrails

> Process, status and number registry: `README.md`. Writing guide: the `/bep-guide` skill.

## Rules

- **A BEP is a tech spec.** Write interfaces, contracts and design decisions. Do not write code line by line.
- **Reserve a number first.** Add the entry to the number registry in `README.md` before creating the document.
- **Refer to the upstream BEP.** An implementation BEP links the motivation or spec BEP and does not rewrite it.
- **Follow the structure of `BEP-0000-template.md`.** Goals, Non-goals, Design, Impact, Implementation Order, References.
- **The template comments set the length limits, and `scripts/knowledge/check_bep_length.py` checks them.** They apply from BEP-1080.

## Goals section

- The first line states what the BEP achieves. Do not write the problem, the background or the defects of the current code.
- A row of the goals table is a capability the BEP provides. Write cleanup of existing code (removing duplication, migration) as a step of the implementation order, not as a goal.
- The "Current" cell holds only the fact that the capability does not exist yet and the path that shows it. Do not list the problems of existing APIs.

## Do not write

- Open questions or a decision log. Settle them in the review and write the result into the design. An item the BEP does not settle goes in Non-goals.
- A summary that repeats earlier sections.

## BEP and PR boundary

The boundary is whether a structural design decision is needed. A structural decision belongs in the BEP even when its effect is internal.

| BEP | PR |
|---|---|
| Component responsibilities and boundaries, layer placement | Dataclass fields, function signatures |
| Observable contracts: meaning of state transitions, API and config fields | File, function and line locations |
| Design decisions and rejected alternatives | Algorithm optimizations, data-structure choices |
| The core flow across layers | Storage locations, wiring details |
