---
name: bep-guide
description: Guide for writing and managing BEPs (Backend.AI Enhancement Proposals) - creation workflow, document segmentation, context-for-ai blocks, Decision Log
version: 1.1.0
tags:
  - bep
  - proposal
  - documentation
  - design
---

# BEP Writing Guide

Guide for creating and managing Backend.AI Enhancement Proposals (BEPs).

This skill is the **process guide** — how to structure, write, and manage BEPs.
The template (`proposals/BEP-0000-template.md`) is the **blank document** to copy and fill in.

## When to Write a BEP

- New feature that spans multiple components
- Architectural change or refactoring
- API design changes (breaking or significant additions)
- New subsystem or plugin
- Changes requiring migration planning

## Workflow

```
1. Reserve Number → 2. Create JIRA → 3. Create Branch → 4. Write BEP → 5. Submit PR → 6. Discussion → 7. Accept/Reject
```

### Step 1: Reserve BEP Number

Edit `proposals/README.md` — add entry to the **BEP Number Registry** table:

```markdown
| 1046 | Your Proposal Title | Your Name | Draft |
```

Numbers start from 1000. Pick the next available number.

### Step 2: Create JIRA Issue

Create a JIRA issue for the BEP and link it in the Related Issues section.

### Step 3: Create Document

**Short BEP (estimated < 500 lines):** Single file.

```bash
cp proposals/BEP-0000-template.md proposals/BEP-XXXX-title.md
```

**Long BEP (estimated >= 500 lines):** Use segmented structure. See [Document Segmentation](#document-segmentation).

### Step 4: Fill Metadata

```yaml
---
Author: Full Name (email@example.com)
Status: Draft
Created: YYYY-MM-DD
Created-Version: YY.Sprint.Patch
Target-Version:
Implemented-Version:
---
```

### Step 5: Write Sections

Each section has a specific purpose. Write in this order:

| Section | Purpose | Length Guide |
|---------|---------|-------------|
| Related Issues | JIRA/GitHub links | 2-5 lines |
| Motivation | Why this change is needed | 10-30 lines |
| Current Design | What exists today | 10-50 lines, include code |
| Proposed Design | The new design | Main body, be specific |
| Migration / Compatibility | Breaking changes, migration plan | 10-30 lines |
| Implementation Plan | Phased steps | 10-30 lines |
| Decision Log | Key decisions with rationale | Append as decisions are made |
| Open Questions | Unresolved items | Update as resolved |
| References | Related docs, BEPs | 2-10 lines |

**Decision Log / Open Questions lifecycle:**
- When an Open Question is resolved, add a row to Decision Log and remove from Open Questions.

### Step 6: Submit PR and Iterate

- Create branch: `bep/XXXX-short-title`
- Submit PR with the BEP document
- Iterate based on review feedback

## Document Segmentation

### When to Segment

Segment a BEP when **any** of these apply:
- Total document exceeds ~500 lines
- Proposed Design has 3+ distinct components
- Implementation Plan has 3+ independent phases
- Document covers multiple subsystems

### Segmented Structure

```
proposals/
├── BEP-XXXX-title.md              # Main: overview + motivation + index (< 200 lines)
└── BEP-XXXX/                     # Directory uses BEP number only
    ├── component-a.md             # Component A detailed design
    ├── component-b.md             # Component B detailed design
    ├── migration.md               # Migration plan (if complex)
    └── diagrams/                  # Images, schemas
```

Main document serves as overview. Directory name uses BEP number only (e.g., `BEP-1046/`).
Use descriptive file names without number prefixes.
Separate `overview.md` file is optional for very large BEPs (5+ sub-documents).

### Main Document (BEP-XXXX-title.md)

The main file must be **concise** (under ~200 lines). It serves as both entry point and overview:

```markdown
---
Author: ...
Status: Draft
---

<!-- context-for-ai
type: master-bep
scope: One-line summary of the proposal
detail-docs: [component-a.md, component-b.md, migration.md]
key-constraints:
  - constraint 1
  - constraint 2
key-decisions:
  - decision 1 (from Decision Log)
phases: 3
-->

# Title

## Related Issues
- JIRA: BA-XXXX

## Motivation
(Why this change is needed - keep under 30 lines)

## Document Index

| Document | Description |
|----------|-------------|
| [component-a](./BEP-XXXX/component-a.md) | Data model and queries |
| [component-b](./BEP-XXXX/component-b.md) | API design and handlers |
| [migration](./BEP-XXXX/migration.md) | Migration plan and compatibility |

## Implementation Plan
1. Phase 1: ...
2. Phase 2: ...

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-15 | Use event-driven over polling | Lower latency, simpler error handling |

## Open Questions
(Unresolved items across all sub-documents — single source of truth)

## References
(Related BEPs, external docs)
```

### Sub-Document Template

Each sub-document is self-contained and focused on one work unit:

```markdown
<!-- context-for-ai
type: detail-doc
parent: BEP-XXXX (Title)
scope: one-line scope description
depends-on: [other-component.md]
key-decisions:
  - reference relevant Decision Log entries in main doc
-->

# BEP-XXXX: Component Name

## Summary
(1-3 sentences: what this component does)

## Current Design
(What exists today for this component)

## Proposed Design
(Detailed design for this component)

## Interface / API
(Public interfaces, data models, function signatures)

## Implementation Notes
(Constraints, dependencies on other components)
```

### Sub-Document Guidelines

- **Each sub-document = one work unit** that can be implemented independently
- Keep each sub-document under ~300 lines
- Include enough context to understand without reading other sub-documents
- Cross-reference other sub-documents by relative link when needed
- Use descriptive file names: `data-model.md`, `config-schema.md`, `event-registration.md`
- **Open Questions go in the main document only** — keeps all unresolved items in one place

## AI Context Block

Add `<!-- context-for-ai -->` to main document and each sub-document. This block is read by AI agents to quickly understand scope and constraints without parsing the entire document. Use key-value format for consistent parsing.

**Main document (`type: master-bep`):**

| Key | Purpose |
|-----|---------|
| `scope` | One-line summary of the proposal |
| `detail-docs` | List of sub-document file names |
| `key-constraints` | Non-goals and hard constraints |
| `key-decisions` | Critical decisions from Decision Log |
| `phases` | Number of implementation phases |

**Sub-document (`type: detail-doc`):**

| Key | Purpose |
|-----|---------|
| `parent` | Parent BEP number and title |
| `scope` | What this document covers |
| `depends-on` | Other sub-documents this depends on |
| `key-decisions` | Relevant Decision Log entries from main doc |

## Status Management

See `proposals/README.md` for the full status lifecycle, transition rules, and version fields.

## AI Agent Working Pattern

These patterns apply when an AI agent (e.g., Claude) works with BEPs.
They also serve as guidelines for humans assigning BEP-related tasks to AI agents.

### Reading an Existing BEP

1. **Read main document first** — get motivation, context-for-ai block, and document index
2. **Read only the relevant sub-document** — based on the task at hand
3. **Check Decision Log** in main document before making implementation choices
4. **Do not read all sub-documents** unless explicitly needed

### Writing a New BEP

1. Check existing BEPs: search `proposals/README.md` registry for related proposals
2. Reserve number in registry
3. Decide structure: single file (< 500 lines) or segmented
4. If segmented: write main document with index first, then sub-documents one at a time
5. Add `<!-- context-for-ai -->` block to every document
6. Each sub-document should be a complete, reviewable unit

### Updating an Existing BEP

1. Read main document to locate the relevant sub-document
2. Read and edit only the targeted sub-document
3. If a question is resolved, move it from Open Questions to Decision Log in main document
4. Update main document index/status if structure changed

### Receiving Implementation Tasks from a BEP

When assigned work based on a BEP:

1. **Read main document** — get context-for-ai block, Decision Log, Implementation Plan
2. **Read only the sub-documents relevant to the assigned phase/scope**
3. **Follow Decision Log** — decisions already made should not be revisited
4. **Check Open Questions** — if your task touches an unresolved item, flag it before proceeding

Example task prompt:
> Implement Phase 1 of BEP-1046.
> Follow the Decision Log in the main document.
> Refer to config-schema.md and event-registration.md for details.

## Cross-References

- `proposals/README.md` — BEP process, number registry, file structure rules
- `proposals/BEP-0000-template.md` — Blank template to copy (sections with example content)
- `/tdd-guide` — Test scenarios for implementation phase
