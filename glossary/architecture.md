# Glossary: Layers and components

The style rules are in the [glossary](../GLOSSARY.md). Korean: [architecture.ko.md](architecture.ko.md)

| English | Meaning | Do not write | Note |
|---|---|---|---|
| accelerator plugin | A plugin package that connects an accelerator to Backend.AI. |   |   |
| account manager | A separate daemon that handles unified user profiles and SSO. | AccountManager, accountmgr |   |
| action | A unit that wraps a service operation to structurally apply permission checks, auditing, and metrics. |   |   |
| adapter | A call layer shared with the GQL layer that a v2 handler calls instead of calling a processor directly. |   |   |
| agent watcher | An add-on service that monitors and manages the Agent service. |   |   |
| app config fragment | A row that stores, as a JSON document, the value a scope adds to an app config key. | AppConfigFragment |   |
| app proxy | A component that dynamically routes and load-balances traffic coming to the service port of a session. | AppProxy, wsproxy, WSProxy, WebSocket Proxy | wsproxy is the old name. Code identifiers are handled separately. |
| app proxy coordinator | An app proxy component that creates routing circuits and places services. |   |   |
| app proxy worker | An app proxy component that forwards traffic. |   |   |
| broadcast event | An event where every subscriber receives the same event. |   |   |
| client SDK | A Python client SDK for Backend.AI. |   |   |
| common | A common package that manager, agent, storage and client SDK all depend on. |   |   |
| console server | A Backend.AI console server that provides cookie-based authentication. |   |   |
| controller | The sole entry point that can change the status of sessions, deployments and more. |   |   |
| DataLoader | A loader that batches multiple node references into one fetch to prevent N+1 queries. | data loader |   |
| deployment history | A record that keeps the status changes and results of each run of the deployment handler. |   |   |
| deployment policy | A policy that holds how a deployment releases a new revision. |   |   |
| deployment preset resource slot | The amount of resources per slot that a deployment preset declares. |   |   |
| deployment revision | A point-in-time snapshot of the deployment configuration, numbered within that deployment. |   |   |
| entity | The data unit that code is divided into, contained within a scope, and pointed to by an action. |   |   |
| entity label | A key=value label that can be attached to any entity. |   |   |
| event bus | An internal service that uses Valkey to track real-time information and notify other components of system events. |   |   |
| kernel runner | A small daemon that runs inside a kernel container and manages user code execution and service processes in the container. | kernel runtime |   |
| kernel scheduling history | A history that records the stages a kernel goes through from image pull to termination and their results. |   |   |
| manager | A component that serves as a central API gateway and orchestrator, receiving user requests, creating sessions and routing code execution to agents. |   |   |
| model card resource requirement | The minimum amount of resources that a model card requires per slot. |   |   |
| processor | A layer that the handler calls, which receives an action and structurally executes permission checks, auditing, and metrics. |   |   |
| prometheus query preset category | A classification that groups prometheus query presets. |   |   |
| relation | A third object that connects or disconnects two entities and has its own table and its own operations. |   |   |
| replica group history | A record that leaves the status changes and results of each run of the replica group handler. |   |   |
| repository | A layer responsible for data access. |   |   |
| resolver | A thin GraphQL operation wrapper layer that calls the fetcher. |   |   |
| route history | A record that leaves the status changes and results of a single run of the route handler for one replica. |   |   |
| scheduler | A sokovan engine that runs the actual scheduling algorithm, which queries waiting sessions and places them on agents. |   |   |
| service | A layer that holds domain validation and business logic. |   |   |
| session agent designation | A feature to designate the agent on which a session is placed. | session designated agent |   |
| session lifecycle handler | A handler that queries sessions in a target status, processes them, and transitions their status based on the result. | lifecycle handler |   |
| sokovan | A layer within the manager that hosts the coordinator and scheduling. |   |   |
| sokovan coordinator | A sokovan component that centrally handles history-based decisions such as retry, timeout, and give_up, along with status transitions. | coordinator |   |
| status transition | A flow in which the status moves according to results such as success, retry, expiration, and giving up. |   |   |
| storage proxy | A proxy component that takes over large file transfers from the manager and abstracts storage vendor APIs. |   |   |
| user fair share | A scheduling priority determined within a resource group by the past usage and weight of a user. |   |   |
| virtual entity | A corresponding row on the permission graph side of an actual entity row. It resides in the virtual_entities table and serves as the basis of entity references and the parent of membership edges. |   |   |
| webserver | A gateway component that provides the web UI and proxies REST and GraphQL requests to the manager or Hive Gateway. |   | A name planned to be changed to gateway in the future. It is kept until the build and service names change. |
