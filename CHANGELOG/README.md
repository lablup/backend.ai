# Changelog index

One file per version branch, holding every release of that branch. Releases up to
26.3.0 are archived in [`../CHANGELOG.md`](../CHANGELOG.md).

## What landed where

Feature headings are taken verbatim from the `Features` section of each release,
newest first. A heading repeated across versions means the feature kept growing;
its first appearance is where it landed.

**Versions released more than a year ago are dropped from this section.** The
cutoff is elapsed time, not whether the branch is still maintained. Files are
never moved, so links keep working.

### [26.8](26.8.md)

**[26.8.0](26.8.md#2680-2026-07-31)** (2026-07-31)

- Reconciler-Based Idle Checking (BEP-1054)
- Scoped App Config (BEP-1052)
- Virtual Scope RBAC Ownership Model (BEP-1062)
- Super-Admin User Impersonation (BEP-1058)
- Resource Group Registration by ID (BEP-1059)
- Session Preemption (BEP-1055)
- DB Record Retention Management (BEP-1063)
- Scheduling History APIs
- Scheduler Dry-Run (Compute Schedule)
- SessionGroup Placement (BEP-1064)
- Agent Re-architecture (BEP-1057)
- Model Serving & Deployment
- Scheduling Policy Controls
- GraphQL DataLoader Extension
- Action Framework Restructuring

### [26.7](26.7.md)

**[26.7.0](26.7.md#2670-2026-07-02)** (2026-07-02)

- Scoped App Config (BEP-1052)
- Reconciler-Based Idle Checking (BEP-1054)
- v2 GraphQL API

### [26.4](26.4.md)

**[26.4.4](26.4.md#2644-2026-06-18)** (2026-06-18)

- Model Serving & Inference Deployment
- RBAC, Roles & Permissions
- RBAC Membership Migration
- Scoped App Config Redesign (BEP-1052)
- Metrics & Observability
- VFolder & Mounts
- Session Scheduling & Resource Management
- v2 API, SDK & CLI
- Development Environment & Installer

**[26.4.0](26.4.md#2640-2026-04-09)** (2026-04-09)

- v2 API, SDK & CLI
- Pydantic DTO v2 Models
- RBAC Permission Enforcement
- Model Serving & Inference Deployment
- Project Admin Page
- Auth & Session Management
- Infrastructure & Operations

## Files

| Version branch | File | Releases |
|---|---|---|
| 26.8 | [`26.8.md`](26.8.md) | 26.8.0 |
| 26.7 | [`26.7.md`](26.7.md) | 26.7.0 |
| 26.4 | [`26.4.md`](26.4.md) | 26.4.0 through 26.4.9 |
| 26.3 and earlier | [`../CHANGELOG.md`](../CHANGELOG.md) | archived before the split |

Patch releases whose `Features` section is a flat list rather than grouped
headings (26.4.2, 26.4.3, 26.4.9) are in the files but not in the index above.
