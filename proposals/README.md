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

### Section Guidelines

| Section | Purpose | Tips |
|---------|---------|------|
| Related Issues | Link to JIRA/GitHub issues | Always include tracking issues |
| Motivation | Explain why this change is needed | Focus on the problem, not the solution |
| Current Design | Describe what exists today | Include code snippets if helpful |
| Proposed Design | Describe the new design | Be specific, include interfaces |
| Migration / Compatibility | Backward compatibility plan | List breaking changes explicitly |
| Implementation Plan | Phased implementation steps | Break into manageable phases |
| Open Questions | Unresolved items | Update as questions are resolved |
| References | Related documents and links | Include related BEPs |

### Best Practices

1. **Be Specific**: Include code examples, interface definitions, and concrete details
2. **Consider Compatibility**: Always document breaking changes and migration paths
3. **Phase Implementation**: Break large changes into smaller, reviewable phases
4. **Track Questions**: Keep Open Questions updated as discussions progress
5. **Link Issues**: Always link related JIRA and GitHub issues

### Template Examples

The template (`BEP-0000-template.md`) includes examples for each section. When creating a new BEP:
1. Copy the template
2. Replace example content with your actual content
3. Remove the "Example:" blocks after writing your content

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
| [1033](BEP-1033/) | Sokovan Handler Test Scenarios | HyeokJin Kim | Draft |
| [1034](BEP-1034-kernel-v2-gql-implementation.md) | KernelV2 GQL Implementation | Gyubong Lee | Draft |
| [1035](BEP-1035-request-id-tracing.md) | Distributed Request ID Propagation | - | Draft |
| [1036](BEP-1036-artifact-storage-quota.md) | Artifact Storage Usage Tracking and Quota Enforcement | Gyubong Lee | Draft |
| [1037](BEP-1037-storage-proxy-health-monitoring.md) | Volume Host Availability Check | Gyubong Lee | Draft |
| [1038](BEP-1038-image-v2-gql-implementation.md) | ImageV2 GQL Implementation | Gyubong Lee | Draft |
| [1039](BEP-1039-image-id-based-service-logic-migration.md) | Image ID Based Service Logic Migration | Gyubong Lee | Draft |
| _next_ | _(reserve your number here)_ | | |

## File Structure

- **Main document**: Always place at root as `BEP-XXXX-title.md`
- **Supporting files** (images, schemas, references): Place in `BEP-XXXX-title/` directory

```
proposals/
├── BEP-1002-agent-architecture.md      # Main document
├── BEP-1002/                           # Supporting files only
│   ├── agent-architecture.png
│   └── kernel-flow.png
├── BEP-1012-RBAC.md                    # Main document
├── BEP-1012-RBAC/                      # Supporting files only
│   ├── api/
│   └── refs/
└── BEP-1018-simple-proposal.md         # No supporting files needed
```
