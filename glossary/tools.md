# Glossary: Technology and tool names

The style rules are in the [glossary](../GLOSSARY.md). Korean: [tools.ko.md](tools.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| Alembic | A tool that applies and rolls back DB schema migrations for Backend.AI components. |   |   |
| Callosum | A ZeroMQ-based library used for RPC between the manager and agents. |   |   |
| cherry-pick | A method of moving changes implemented first in main to an x.y release branch. |   |   |
| deep merge | A merge that combines all fragments visible to the caller in ascending allow-list rank, recursing into nested objects while replacing scalars and lists as a whole. |   |   |
| distributed lock | A distributed locking backend that the manager can replace, chosen among filelock, pg_advisory, redlock, etcd and etcetra, with pg_advisory as the default. | replacible distributed lock backend |   |
| Docker backend | A backend implementation where the agent handles kernel containers with docker among multiple container runtimes. |   |   |
| Docker Swarm | A foundation used to build the overlay network of a multi-node multi-kernel session. | Swarm |   |
| dotfile | A collection of user configuration files set on an entity. |   |   |
| etcd | A configuration source that holds cluster-wide settings and manager state and hot reloads on change. |   |   |
| FastTrack | An add-on service that designs and runs compute task pipelines on top of the manager. |   |   |
| Forklift | A standalone service that builds and imports Backend.AI compatible container images. |   |   |
| Graphene | A subgraph that provides the manager's legacy GraphQL API and is being migrated to Strawberry. | Legacy GraphQL API |   |
| GraphQL Inspector | A CI status check that inspects the GraphQL schema for breaking changes. |   |   |
| Hive Gateway | A GraphQL gateway that federates the three GQL subgraphs of the manager (graphene, strawberry, public). | Hive Router |   |
| jail | A kernel execution environment that blocks some system calls according to policy. | Backend.AI Jail |   |
| Kubernetes backend | A backend that handles kubernetes among the infrastructure implementations of an agent. | k8s |   |
| mock accelerator | A simulator plugin that makes an accelerator device appear present without real hardware. | mock, mock-up plugin, mocked Accelerators |   |
| Pants | A build tool that handles build automation and dependency management. | Pantsbuild |   |
| presigned URL | A URL with an expiration time that allows direct upload to or download from object storage. |   |   |
| Prometheus | A monitoring tool that collects operational metrics of components such as the manager. |   |   |
| pydantic | A library used as the validator for REST API requests and responses since 24.03. |   |   |
| SDK | A python library that uses the Backend.AI REST API. |   |   |
| strawberry | A subgraph that provides the v2 GraphQL API of the Manager. | New GraphQL API, v2 schema |   |
| towncrier | A tool that collects changelog fragments in changes/ to build a changelog. |   |   |
| Traefik | A proxy that handles traffic forwarding instead of the worker and reads routes that the coordinator publishes. | proxy dataplane |   |
| TUS | A resumable upload method in which the proxy manages offsets with a Valkey lease. | upload session |   |
| Valkey | A dependency that holds cache data and also serves as an event queue. | Redis | This is the documentation spelling. Changing config keys and code names is a separate task. |
| VFS storage | A filesystem backend behind a storage namespace. |   |   |
