# BEPs
Backend.AI Enhancement Proposals

## Process

1. **Reserve a BEP number** by adding your proposal to the [BEP Number Registry](#bep-number-registry) table below.
2. Create a new branch and pull request for creation.
   - Copy `proposals/BEP-0000-template.md` to create a new document with your reserved number.
   - Write and submit the draft.
3. Discuss with other developers and maintainers in the PR.
4. Submit multiple pull requests to modify and update your proposals.
5. Once accepted, update the document status to "Accepted" with the target version.
   - You may further submit additional pull requests to revise the document when there are changes required found during actual implementation work.
6. Once implementation is complete, update the status to "Implemented" with the actual version.

## Status Lifecycle

```
Draft ──────→ Accepted ──→ Implemented
  │              │
  └─→ Rejected ←─┘
```

| Status | Description |
|--------|-------------|
| Draft | Initial proposal, under discussion |
| Accepted | Approved for implementation, target version assigned |
| Implemented | Implementation complete, actual version recorded |
| Rejected | Proposal was rejected or cancelled |

### Status Transition Rules

| From | To | When | Required Actions |
|------|-----|------|------------------|
| Draft | Accepted | Proposal approved by maintainers | Set `Target-Version` |
| Draft | Rejected | Proposal rejected after discussion | Document rejection reason |
| Accepted | Implemented | Implementation merged to main | Set `Implemented-Version` |
| Accepted | Rejected | Implementation cancelled | Document cancellation reason |

## Version Fields

BEP documents track three version milestones:

| Field | When to Fill | Example |
|-------|--------------|---------|
| Created-Version | When first creating the BEP | 26.1.0 |
| Target-Version | When status changes to Accepted | 26.2.0 |
| Implemented-Version | When status changes to Implemented | 26.2.1 |

Version format: `YY.Sprint.Patch` (e.g., 26.1.0 = Year 2026, Sprint 1, Patch 0)

## Writing Guide

For section structure, Decision Log lifecycle, AI context blocks,
and document segmentation details, see the `/bep-guide` skill.

### Quick Reference

1. Copy `proposals/BEP-0000-template.md`
2. Fill metadata (Author, Status, Created, Created-Version)
3. Write sections in order: Motivation → Current → Proposed → Migration → Plan
4. Submit PR on branch `bep/XXXX-short-title`

## BEP Number Registry

To prevent number conflicts, **always reserve your BEP number here first** before creating the document.
When multiple people add entries simultaneously, Git merge conflicts will naturally prevent duplicate numbers.

BEP numbers start from 1000.

| Number | Title | Author | Status |
|--------|-------|--------|--------|
| [1000](BEP-1000-redefining-accelerator-metadata.md) | Redefining Accelerator Metadata | Joongi Kim | Draft |
| [1001](BEP-1001-app-injection.md) | App Injection | Joongi Kim | Draft |
| [1002](BEP-1002-agent-architecture.md) | Agent Architecture | HyeokJin Kim | Draft |
| [1003](BEP-1003-define-test-scenario-verifying-agent-functionality.md) | Test Scenario for Agent Functionality | Bokeum Kim | Draft |
| [1004](BEP-1004-scenario-tester.md) | Scenario Tester | HyeokJin Kim | Draft |
| [1005](BEP-1005-unified-appproxy.md) | Unified AppProxy | Kyujin Cho | Draft |
| [1006](BEP-1006-service-deployment-strategy.md) | Service Deployment Strategy | Jeongseok Kang | Accepted |
| [1007](BEP-1007-storage-agent.md) | Storage Agent | Joongi Kim | Draft |
| [1008](BEP-1008-RBAC.md) | RBAC | HyeokJin Kim | Draft |
| [1009](BEP-1009-model-serving-registry.md) | Model Serving Registry | HyeokJin Kim | Draft |
| [1010](BEP-1010-new-gql.md) | New GQL | - | Accepted |
| 1011 | _(skipped)_ | | |
| [1012](BEP-1012-RBAC.md) | RBAC (detailed) | Sanghun Lee | Draft |
| [1013](BEP-1013-GraphQL-schema-for-new-model-service.md) | GraphQL Schema for New Model Service | Bokeum Kim | Accepted |
| [1014](BEP-1014-preemption-of-low-priority-sessions.md) | Preemption of Low Priority Sessions | Joongi Kim | Draft |
| [1015](BEP-1015-keypair-user-project-resource-policy-reorg.md) | Keypair/User/Project Resource Policy Reorg | Joongi Kim | Draft |
| [1016](BEP-1016-accelerator-interface-v2.md) | Accelerator Interface v2 | Joongi Kim | Draft |
| [1017](BEP-1017-model-scanner-model-downloader.md) | Model Scanner and Downloader | Bokeum Kim | Accepted |
| [1018](BEP-1018-local-cache-for-model-vfolders.md) | Local Cache for Model VFolders | Joongi Kim | Draft |
| [1019](BEP-1019-minio-artifact-registry-storage.md) | MinIO Artifact Registry Storage | Gyubong Lee | Accepted |
| [1020](BEP-1020-vfolder-destination-support-for-artifact-import.md) | VFolder Destination Support for Artifact Import | Gyubong Lee | Draft |
| [1021](BEP-1021-gql-string-filter-enhancement.md) | GQL StringFilter Enhancement | HyeokJin Kim | Implemented |
| [1022](BEP-1022-pydantic-field-annotations.md) | Pydantic Field Metadata Annotation | HyeokJin Kim | Implemented |
| [1023](BEP-1023-unified-config-consolidation.md) | UnifiedConfig Consolidation & Loader/CLI | HyeokJin Kim | Draft |
| [1024](BEP-1024-agent-rpc-connection-pooling.md) | Agent RPC Connection Pooling | HyeokJin Kim | Implemented |
| [1025](BEP-1025-server-side-csv-export.md) | Server-Side CSV Export API | HyeokJin Kim | Draft |
| [1026](BEP-1026-fair-share-scheduler.md) | Fair Share Scheduler | HyeokJin Kim | Draft |
| 1027 | Docker Relay in Compute Sessions | Joongi Kim | Draft |
| [1028](BEP-1028-kubernetes-bridge.md) | Kubernetes Bridge | Daemyung Kang, Hyunhoi Koo | Draft |
| [1029](BEP-1029-sokovan-observer-handler.md) | Sokovan ObserverHandler Pattern | HyeokJin Kim | Draft |
| [1030](BEP-1030-sokovan-scheduler-status-transition.md) | Sokovan Scheduler Status Transition Design | HyeokJin Kim | Draft |
| [1031](BEP-1031-graphql-field-metadata.md) | GraphQL API Field Metadata Extension | HyeokJin Kim | Draft |
| [1032](BEP-1032-unified-input-validation.md) | Unified Input Validation for REST and GraphQL | HyeokJin Kim | Draft |
| [1033](BEP-1033-sokovan-handler-test-scenarios.md) | Sokovan Handler Test Scenarios | HyeokJin Kim | Draft |
| [1034](BEP-1034-kernel-v2-gql-implementation.md) | KernelV2 GQL Implementation | Gyubong Lee | Draft |
| [1035](BEP-1035-request-id-tracing.md) | Distributed Request ID Propagation | Gyubong Lee | Draft |
| [1036](BEP-1036-artifact-storage-quota.md) | Artifact Storage Usage Tracking and Quota Enforcement | Gyubong Lee | Rejected |
| [1037](BEP-1037-storage-proxy-health-monitoring.md) | Volume Host Availability Check | Gyubong Lee | Draft |
| [1038](BEP-1038-image-v2-gql-implementation.md) | ImageV2 GQL Implementation | Gyubong Lee | Draft |
| [1039](BEP-1039-image-id-based-service-logic-migration.md) | Image ID Based Service Logic Migration | Gyubong Lee | Draft |
| [1040](BEP-1040-multiple-path-zip-download-implementation.md) | Multiple Files Download in ZIP | TaekYoung Kwon | Draft |
| [1041](BEP-1041-scope-based-graphql-api-naming.md) | Scope-Based GraphQL API Naming Convention | HyeokJin Kim | Draft |
| [1042](BEP-1042-mypy-strict-mode-migration.md) | MyPy Strict Mode Migration | HyeokJin Kim | Draft |
| [1043](BEP-1043-scope-types.md) | Scope Types Description | Sanghun Lee | Draft |
| [1044](BEP-1044-multi-agent-device-split.md) | Multi-Agent Device Split | Hyunhoi Koo | Draft |
| [1045](BEP-1045-prometheus-client-extraction-and-querier-interface-abstraction.md) | Prometheus Client Extraction and Querier Interface Abstraction | BoKeum Kim | Draft |
| [1046](BEP-1046-unified-service-discovery.md) | Unified Service Discovery with DB-backed Service Catalog | HyeokJin Kim | Draft |
| [1047](BEP-1047-resource-slot-db-normalization.md) | Resource Slot DB Normalization | HyeokJin Kim | Draft |
| [1048](BEP-1048-RBAC-entity-relationship-model.md) | RBAC Entity Relationship Model | Sanghun Lee | Draft |
| [1049](BEP-1049-zero-downtime-deployment.md) | Model Service Zero-downtime deployment architecture | Gyubong Lee | Draft |
| _next_ | _(reserve your number here)_ | | |

## File Structure

### Single-File BEP (< 500 lines)

For short proposals, use a single markdown file:

```
proposals/
└── BEP-1018-simple-proposal.md         # All content in one file
```

### Segmented BEP (>= 500 lines)

When a BEP exceeds ~500 lines or covers 3+ distinct components, split into a **main document + sub-documents**. Each sub-document should represent one independent work unit.

**Segmentation criteria** (any one triggers):
- Total document exceeds ~500 lines
- Proposed Design has 3+ distinct components
- Implementation Plan has 3+ independent phases
- Document covers multiple subsystems

```
proposals/
├── BEP-XXXX-title.md              # Main: overview + motivation + index (< 200 lines)
└── BEP-XXXX/                     # Sub-documents and supporting files
    ├── component-a.md             # Component A detailed design (one work unit)
    ├── component-b.md             # Component B detailed design (one work unit)
    ├── migration.md               # Migration plan (if complex)
    └── diagrams/                  # Images, schemas
```

**Directory naming rule**: Use BEP number only (e.g., `BEP-1002/`), not the full title.

**Registry link rule**: Always link to the main `.md` file, not the directory.

**Main document role**: Concise entry point serving as overview — metadata, motivation, document index table, Decision Log, and Open Questions. Keep under ~200 lines.

**Sub-document rules**:
- Each sub-document = one work unit (implementable independently)
- Keep each under ~300 lines
- Self-contained: include enough context to understand without reading others
- Use descriptive file names: `data-model.md`, `config-schema.md`, `event-registration.md`
- Cross-reference other sub-documents by relative link
- Open Questions go in the main document only (single source of truth)

### Supporting Files Only

For BEPs that are single-file but need images or schemas:

```
proposals/
├── BEP-1002-agent-architecture.md      # Main document (single file)
├── BEP-1002/                           # Supporting files only
│   ├── agent-architecture.png
│   └── kernel-flow.png
└── BEP-1012-RBAC.md                    # Main document (single file)
```

For detailed writing workflow, see `/bep-guide` skill.
