# BEPs
Backend.AI Enhancement Proposals

## Process

1. **Reserve a BEP number** by adding your proposal to the [BEP Number Registry](#bep-number-registry) table below.
2. Create a new branch and pull request for creation.
   - Copy `proposals/BEP-0000-template.md` to create a new document with your reserved number.
   - Write and submit the draft.
3. Discuss with other developers and maintainers in the PR.
4. Submit multiple pull requests to modify and update your proposals.
5. Once accepted, update the document status to "Accepted" with the target LTS release version.
   - You may further submit additional pull requests to revise the document when there are changes required found during actual implementation work.

## BEP Number Registry

To prevent number conflicts, **always reserve your BEP number here first** before creating the document.
When multiple people add entries simultaneously, Git merge conflicts will naturally prevent duplicate numbers.

| Number | Title | Author | Status |
|--------|-------|--------|--------|
| [1000](BEP-1000-redefining-accelerator-metadata.md) | Redefining Accelerator Metadata | - | Draft |
| [1001](BEP-1001-app-injection.md) | App Injection | - | Draft |
| [1002](BEP-1002-agent-architecture.md) | Agent Architecture | - | Draft |
| [1003](BEP-1003-define-test-scenario-verifying-agent-functionality.md) | Test Scenario for Agent Functionality | - | Draft |
| [1004](BEP-1004-scenario-tester.md) | Scenario Tester | - | Draft |
| [1005](BEP-1005-unified-appproxy.md) | Unified AppProxy | - | Draft |
| [1006](BEP-1006-service-deployment-strategy.md) | Service Deployment Strategy | - | Accepted |
| [1007](BEP-1007-storage-agent.md) | Storage Agent | - | Draft |
| [1008](BEP-1008-RBAC.md) | RBAC | - | Draft |
| [1009](BEP-1009-model-serving-registry.md) | Model Serving Registry | - | Draft |
| [1010](BEP-1010-new-gql.md) | New GQL | - | Accepted |
| [1012](BEP-1012-RBAC.md) | RBAC (detailed) | - | Draft |
| [1013](BEP-1013-GraphQL-schema-for-new-model-service.md) | GraphQL Schema for New Model Service | - | Accepted |
| [1014](BEP-1014-preemption-of-low-priority-sessions.md) | Preemption of Low Priority Sessions | - | Draft |
| [1015](BEP-1015-keypair-user-project-resource-policy-reorg.md) | Keypair/User/Project Resource Policy Reorg | - | Draft |
| [1016](BEP-1016-accelerator-interface-v2.md) | Accelerator Interface v2 | - | Draft |
| [1017](BEP-1017-model-scanner-model-downloader.md) | Model Scanner and Downloader | Bokeum Kim | Accepted |
| [1018](BEP-1018-local-cache-for-model-vfolders.md) | Local Cache for Model VFolders | Joongi Kim | Draft |
| [1019](BEP-1019-minio-artifact-registry-storage.md) | MinIO Artifact Registry Storage | Gyubong Lee | Accepted |
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

## Rules for PR title

Each PR either creates or updates the BEP documents with the squash-merge strategy.
Please put the high-level summary of the update in the PR title as they will become the commit message of the main branch.
Individual commits inside each PR may be freely titled.

Examples:

* "BEP-9999 (new): A shiny new feature" (with the document title)
* "BEP-9999 (update): Change the implementation plan" (with the summary of change)
* "BEP-9999 (update): Remove unnecessary API changes" (with the summary of change)
* "BEP-9999 (accept): Planned for 25.9 LTS" (with the target version)
* "BEP-9999 (reject): Decided to drop because ..." (with the short description of rejection)
* "BEP-9999 (revise): Update integration with ZZZ subsytem" (with the summary of revision)
