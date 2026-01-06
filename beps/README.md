는데.# BEPs
Backend.AI Enhancement Proposals

## Process

1. **Reserve a BEP number** by adding your proposal to the [BEP Number Registry](#bep-number-registry) table below.
2. Create a new branch and pull request for creation.
   - Copy `beps/proposals/BEP-0000-template.md` to create a new document with your reserved number.
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
| 1000 | Redefining Accelerator Metadata | - | Draft |
| 1001 | App Injection | - | Draft |
| 1002 | Agent Architecture | - | Draft |
| 1003 | Test Scenario for Agent Functionality | - | Draft |
| 1004 | Scenario Tester | - | Draft |
| 1005 | Unified AppProxy | - | Draft |
| 1006 | Service Deployment Strategy | - | Accepted |
| 1007 | Storage Agent | - | Draft |
| 1008 | RBAC | - | Draft |
| 1009 | Model Serving Registry | - | Draft |
| 1010 | New GQL | - | Accepted |
| 1012 | RBAC (detailed) | - | Draft |
| 1013 | GraphQL Schema for New Model Service | - | Accepted |
| 1014 | Preemption of Low Priority Sessions | - | Draft |
| 1015 | Keypair/User/Project Resource Policy Reorg | - | Draft |
| 1016 | Accelerator Interface v2 | - | Draft |
| 1017 | Model Scanner and Downloader | Bokeum Kim | Accepted |
| 1018 | Local Cache for Model VFolders | Joongi Kim | Draft |
| 1019 | MinIO Artifact Registry Storage | Gyubong Lee | Accepted |
| 1020 | VFolder Destination Support for Artifact Import | Gyubong Lee | Draft |
| _next_ | _(reserve your number here)_ | | |

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
