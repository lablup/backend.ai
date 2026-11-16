# Glossary: Infrastructure

The style rules are in the [glossary](../GLOSSARY.md). Korean: [infrastructure.ko.md](infrastructure.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| AppProxy tunnel | An AppProxy path used to access a container. | App Proxy tunnel |   |
| bai | A command of the Backend.AI v2 CLI. | v2 CLI |   |
| BEP | Backend.AI Enhancement Proposal, a proposal document that contains the design background. |   |   |
| Event Stream API | A manager API that emits events via Server-Sent Events. | Server-Sent Events |   |
| halfstack | A development environment setup launched with Docker Compose that includes PostgreSQL, etcd, and Valkey containers. | Backend.AI halfstack |   |
| installer channel | An installation channel determined by reading the latest maintained version and the latest LTS from the registry. |   |   |
| local config | A TOML configuration of each component that is read at boot and applied only after a restart. |   |   |
| LTS | A release line promised to be supported for one year. | long-term support |   |
| management node | A node that installs most components except the agent. |   |   |
| mount path | The path where a vfolder is mounted in a container. |   |   |
| overlay network | A network that the manager automatically configures for a multi-kernel session spanning multiple agents. | private overlay network |   |
| private bridge network | A network in which the containers of a single-node multi-kernel session communicate privately. |   |   |
| profile | A unit of CLI connection information that stores an endpoint, an account, and a session together. |   |   |
| RC | A release type value that stands for a release candidate. | Release Candidate |   |
| resource-seconds | A usage unit obtained by multiplying the resource amount by the seconds of the usage period, not mixed with the raw unit of capacity. |   |   |
| stable | A channel that points to the latest LTS version among installer download links. |   |   |
| storage backend | A normalized record that refers to the storage appliance where a storage volume resides. |   |   |
| storage backend type | An implementation of a storage backend that can serve a volume. |   |   |
| v1 CLI | A legacy CLI separate from the v2 CLI. Do not use it. |   |   |
| WebUI | A web client that mainly consumes the manager's GraphQL API. |   |   |
