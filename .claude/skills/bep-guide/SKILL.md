---
name: bep-guide
description: Guide for writing and managing BEPs (Backend.AI Enhancement Proposals) - creation workflow, template sections and length limits, document segmentation, context-for-ai blocks
version: 1.2.0
tags:
  - bep
  - proposal
  - documentation
  - design
---

# BEP Writing Guide

Guide for creating and managing Backend.AI Enhancement Proposals (BEPs).

- Rules for the content: `proposals/AGENTS.md`.
- The blank document to copy: `proposals/BEP-0000-template.md` (sections, placeholders and length limits).
- This skill: the workflow, segmentation and the AI context block.

## When to Write a BEP

- New feature that spans multiple components
- Architectural change or refactoring
- API design changes (breaking or significant additions)
- New subsystem or plugin
- Changes requiring migration planning

## Workflow

```
1. Reserve number → 2. Create issue → 3. Create branch → 4. Write BEP → 5. Review → 6. Submit PR → 7. Accept/Reject
```

### Step 1: Reserve BEP Number

Add an entry to the **BEP Number Registry** table in `proposals/README.md`:

```markdown
| 1046 | Your Proposal Title | Your Name | Draft |
```

Numbers start from 1000. Pick the next available number.

### Step 2: Create Issue

Create an issue for the BEP and list it in the Related issue cells of the goals table.

### Step 3: Create Document

```bash
cp proposals/BEP-0000-template.md proposals/BEP-XXXX-title.md
cp proposals/BEP-0000-template.ko.md proposals/BEP-XXXX-title.ko.md
```

Over 300 lines, use the segmented structure. See Document Segmentation below.

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

Write in the template order: Goals, Non-goals, Design, Impact, Implementation Order, References.

| Section | Holds |
|---|---|
| Goals | What the BEP achieves, and a table of the capabilities it provides with the current state, the done condition and the issue |
| Non-goals | Items the BEP does not cover or settle, and where they are covered |
| Design | One subsection per component that resolves a goal: an SVG, contract tables, a short explanation and the rejected alternative |
| Impact | Compatibility, permission, performance and metrics, only when they apply |
| Implementation Order | One step per issue, each with the goal or result it resolves |
| References | Related BEPs and documents |

- The template comments set the length limits. `scripts/knowledge/check_bep_length.py` checks them from BEP-1080.
- Settle open questions in the review and write the result into the design. The BEP keeps no decision log.
- Before requesting the review, run `/glossary-review`.

### Step 6: Submit PR and Iterate

- Create branch: `bep/XXXX-short-title`
- Submit the PR with both language files
- Iterate based on review feedback

## English and Korean Pairs

A BEP is a pair in the same folder: English `BEP-NNNN-title.md` and Korean `BEP-NNNN-title.ko.md`.
Each sub-document of a segmented BEP is a pair too, such as `component-a.md` and `component-a.ko.md`.

- Frontmatter goes only in the English file.
- Both files keep the same headings in the same order.
- Update both files in the same change.
- `scripts/knowledge/check_bilingual.py` validates the pairs.

## Document Segmentation

### When to Segment

Segment a BEP when **any** of these apply:
- Total document exceeds 300 lines
- Design has 3+ distinct components
- Implementation Order has 3+ independent steps
- Document covers multiple subsystems

### Segmented Structure

```
proposals/
├── BEP-XXXX-title.md              # Main: goals, non-goals, index (< 200 lines)
└── BEP-XXXX/                     # Directory uses BEP number only
    ├── component-a.md             # Component A design
    ├── component-b.md             # Component B design
    └── <diagram-name>.svg         # Diagrams
```

Directory name uses the BEP number only (e.g., `BEP-1046/`). Use descriptive file names without number prefixes.

### Main Document (BEP-XXXX-title.md)

The main file holds the context-for-ai block, Goals, Non-goals, the Document Index, Implementation Order and References:

```markdown
<!-- context-for-ai
type: master-bep
scope: One-line summary
detail-docs: [component-a.md, component-b.md]
key-constraints: [non-goal 1, constraint 1]
phases: 3
-->

# Title

## Document Index

| Document | Description |
|----------|-------------|
| [component-a](./BEP-XXXX/component-a.md) | Data model and queries |
| [component-b](./BEP-XXXX/component-b.md) | API design and handlers |
```

### Sub-Document Template

Each sub-document follows the Design section of the template for one work unit:

```markdown
<!-- context-for-ai
type: detail-doc
parent: BEP-XXXX (Title)
scope: one-line scope description
depends-on: [other-component.md]
-->

# BEP-XXXX: Component Name

## Design
(Subsections as in the template's Design section)

## Impact
(Only when it applies)
```

### Sub-Document Guidelines

- **Each sub-document = one work unit** that can be implemented independently
- The same length limits apply to each sub-document
- Include enough context to understand without reading other sub-documents
- Cross-reference other sub-documents by relative link when needed

## AI Context Block

Add `<!-- context-for-ai -->` to the main document and each sub-document of a segmented BEP. AI agents read it to understand scope and constraints without parsing the whole document.

| Key | Document | Purpose |
|-----|---|---------|
| `scope` | both | One-line summary |
| `detail-docs` | main | Sub-document file names |
| `key-constraints` | main | Non-goals and hard constraints |
| `phases` | main | Number of implementation steps |
| `parent` | sub | Parent BEP number and title |
| `depends-on` | sub | Other sub-documents this depends on |

## Status Management

See `proposals/README.md` for the status lifecycle, transition rules and version fields.

## AI Agent Working Pattern

### Reading an Existing BEP

1. **Read the main document first**: goals, non-goals, context-for-ai block and document index
2. **Read only the relevant sub-document** for the task at hand

### Updating an Existing BEP

1. Read the main document to locate the relevant sub-document
2. Edit only the targeted sub-document, and both language files
3. Update the main document index if the structure changed

### Receiving Implementation Tasks from a BEP

1. **Read the main document**: goals, non-goals, Implementation Order
2. **Read only the sub-documents of the assigned step**
3. **Follow the design.** If the task needs a decision the design does not make, raise it before proceeding

## Cross-References

- `proposals/AGENTS.md`: content rules
- `proposals/README.md`: process, number registry, file structure
- `proposals/BEP-0000-template.md`: template with placeholders and length limits
- `/glossary-review`: glossary review before the review request
- `/test-guide`: test scenarios for the implementation step
