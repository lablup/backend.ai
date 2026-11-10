# Glossary: Process and documents

The style rules are in the [glossary](../GLOSSARY.md). Korean: [process.ko.md](process.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| additive only | A v2 schema policy that only adds new fields and deprecates existing fields without changing field names or purposes. |   |   |
| agent heartbeat | A signal by which an agent periodically notifies the manager of its availability. | heartbeat |   |
| AGENTS.md | A document that contains only rules for AI coding agents. |   |   |
| backfill | The work of pre-filling existing data so that a new feature can use it. |   |   |
| background task | A long-running job that is processed asynchronously, issues a task id, and notifies completion via an event. | bgtask |   |
| backport | The process of moving changes merged into main to a release branch. |   |   |
| blue-green deployment | A deployment method that keeps the existing deployment as Blue and switches traffic to a new deployment. |   |   |
| changelog fragment | A per-PR summary file placed under changes/ and included in release notes via towncrier. | news fragment |   |
| CSV export | An operation that downloads data as a CSV by specifying fields and filters per domain. |   |   |
| delegation | A feature that passes a scan or import request to another Reservoir so that it performs the cross operation on behalf of the requester. | Delegate Import, Delegate Scan |   |
| health check | A check that verifies whether a model service is healthy. |   |   |
| KNOWLEDGE.md | A document that holds background knowledge and the rationale for decisions. |   |   |
| maintained version | A release version listed in `.github/maintained-versions.yml` to which fix PRs are automatically backported. |   |   |
| major upgrade | A cluster upgrade that includes feature additions and structural changes. |   |   |
| minor upgrade | A cluster upgrade that raises the version while keeping the major version. |   |   |
| monorepo | A development repository layout that keeps the backend stack in a single repository. | mono-repo, mono-repository, semi-mono repository |   |
| preemption | A feature that displaces a running session of lower priority to place other sessions when resources are insufficient. |   |   |
| release branch | A branch name in the x.y form created every 6 months for each major release. |   |   |
| release tag | A tag name in the x.y.z format created for each patch release. |   |   |
| retention policy | A rule that purges records past the retention period, one per category. |   |   |
| revision merge chain | A merge chain that fills model definition fields left empty by the request in order from the lowest priority: the model_mount_destination default, the runtime variant baseline, the revision preset, deployment-config.yaml, model-definition.yaml, and override. | merge chain |   |
| scenario | A test unit that runs one adapter against a real database and Valkey to verify what a single request returns. |   |   |
| scheduling history | A record that stores the phase, status changes, result, and attempt count for each scheduling attempt of a session. |   |   |
| seed | A feature where the mgr seed command fills initial rows with YAML files under seeds/. |   | In test code, `TestSeeder` and `seed.within` are code names for storing test data in advance. |
| service catalog heartbeat | A signal that renews the liveness of a service catalog entry. | heartbeat |   |
| service discovery | A feature where an agent registers itself with the cluster via etcd and announces service instance registration as an event. | SD |   |
| skill | A guidance document that Claude Code calls for development tasks. |   |   |
| sweep | An operation in which a retention policy cleans up its own category. | swept |   |
| usage bucket | A record of resource usage that one scope consumed in one resource group over one period. |   |   |
