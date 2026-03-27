---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-02-07
Created-Version: 26.3.0
Target-Version:
Implemented-Version:
---

<!-- context-for-ai
type: master-bep
scope: Unified service discovery design for all Backend.AI components
detail-docs: [data-model.md, config-schema.md, event-registration.md, cli-migration.md, client-pool.md]
key-decisions:
  - Redis Event as transport channel, DB as authoritative store
  - role+scope based multi-endpoint model
  - Config-driven endpoint registration (with CLI migration tool)
  - Self-preservation for failure resilience (Eureka pattern)
  - Agent multi-agent: minimize SD scope (sub-concept)
  - instance_id: SD config first, component-specific fallback, auto-generation
implementation: 4 phases, BA-4315~4318
-->

# Unified Service Discovery with DB-backed Service Catalog

## Related Issues

- JIRA Epic: BA-4313
- JIRA: BA-4314 (BEP), BA-4315 (Foundation), BA-4316 (CLI Migration), BA-4317 (Runtime), BA-4318 (Client Pool)

## Detailed Document Index

| Document | Contents | Related Phase |
|----------|----------|---------------|
| [Data Model](BEP-1046/data-model.md) | DB DDL, role/scope definitions and details | Phase 1 |
| [Config Schema](BEP-1046/config-schema.md) | TOML config examples, Pydantic models, instance_id per-component rules | Phase 1 |
| [Event & Registration Flow](BEP-1046/event-registration.md) | Event type definitions, registration flow details, config_hash optimization, per-component capabilities | Phase 1, 3 |
| [CLI Migration](BEP-1046/cli-migration.md) | CLI usage, per-component mapping rules, output examples | Phase 2 |
| [Client Pool & Query API](BEP-1046/client-pool.md) | ServiceCatalogCache, SDClientPool, existing address transition strategy, GraphQL query API | Phase 4 |

## Motivation

Backend.AI's current service discovery (SD) uses different mechanisms per component, lacks consistency, and makes it difficult to query and expose service status to users.

**Current state:**

| Component | SD Registration | How other services discover it |
|-----------|----------------|-------------------------------|
| Agent | Heartbeat event → Manager → `agents` table | Manager queries DB |
| Manager | `ServiceDiscoveryLoop` (ETCD/Redis) | Webserver directly sets address in config |
| Storage Proxy | `ServiceDiscoveryLoop` (ETCD/Redis) | Manager reads address from etcd config |
| AppProxy Coordinator | `ServiceDiscoveryLoop` (Redis only) | Manager uses `wsproxy_addr` from `scaling_groups` row |
| AppProxy Worker | `ServiceDiscoveryLoop` (Redis only) | Worker requests Coordinator for connection |
| Webserver | Not registered | No server needs to discover it |

**Problems:**

1. **Inadequate query method**: SD data stored in Redis hash or etcd is hard to expose to users in a structured way
2. **Lack of consistency**: Agent uses events, others use `ServiceDiscoveryLoop`, AppProxy address is in scaling_group row, Manager address is hardcoded in config — all different approaches
3. **No endpoint model**: Services have multiple endpoints for different roles (API, RPC, metrics) and network contexts (container, cluster, public), but there is no structure to represent this
4. **Client pool not integrated**: `AgentClientPool` and `ClientPool` are not connected to SD, requiring manual address injection
5. **Lack of failure resilience**: Risk of SD data loss on Redis/etcd failure

## Current Design

<details>
<summary>Current ServiceDiscoveryLoop code (reference)</summary>

```python
class ServiceDiscoveryLoop:
    async def start(self):
        await self._service_discovery.register(self._service_metadata)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())  # 60s

    async def stop(self):
        await self._service_discovery.unregister(...)
```

- Redis backend: stores hash at `service_discovery.{group}.{id}` key with 3min TTL
- ETCD backend: stores at `ai/backend/service_discovery/{group}/{id}` prefix

</details>

<details>
<summary>Current endpoint model (reference)</summary>

The current `ServiceEndpoint` represents only a single address, but each component actually has multiple addresses:

- **Agent**: `rpc_listen_addr`, `advertised_rpc_addr`, `service_addr`, `announce_internal_addr`
- **Storage Proxy**: `client.service_addr`, `manager.service_addr`, `manager.announce_addr`, `manager.announce_internal_addr`
- **AppProxy Worker**: `api_bind_addr`, `api_advertised_addr`, `wildcard_domain.bind_addr`, `port_proxy.bind_host`

</details>

- Agent publishes `AgentHeartbeatEvent` via Redis Stream anycast → Manager syncs to `agents` table
- Other components register via `ServiceDiscoveryLoop` to Redis/ETCD
- Endpoint model is single-address structure, unable to represent multiple addresses

## Proposed Design

### Design Principles

1. **Redis events as transport channel**: Reuse existing Redis Stream event infrastructure
2. **DB as authoritative store**: Enables SQL queries, GraphQL exposure, audit trails
3. **role + scope based multi-endpoint**: Distinguish by role (what the endpoint is for) and scope (where it's accessed from)
4. **Config-driven**: Explicit declaration via `[service-discovery.endpoints]` section. CLI migration tool provided
5. **Self-preservation**: Freeze last known state on backend failure to prevent service eviction (Netflix Eureka pattern)

### Data Model

Composed of `service_catalog` + `service_catalog_endpoint` tables. Each service is identified by `(service_group, instance_id)`, and endpoints represent multiple addresses via `(role, scope)` combinations.

- **role**: Functional purpose of the endpoint — `api`, `rpc`, `metrics`, `client-api`, `internal-api`
- **scope**: Network access context — `cluster`, `container`, `public`

> DDL and role/scope details → [Data Model Details](BEP-1046/data-model.md)

### instance_id Strategy

A stable identifier that persists across service restarts. Uses config `instance-id` as first priority; falls back to component-specific rules if omitted. Services with multiple instances (Storage Proxy, AppProxy Coordinator) must explicitly set it in config.

> Per-component rules and code → [Config Schema](BEP-1046/config-schema.md#instance_id-strategy)

### Registration Flow Overview

```
Startup → Read config + compute config_hash
        → Publish ServiceRegisteredEvent (Redis Stream anycast)
        → Manager consumes → DB UPSERT

Heartbeat (60s) → Compare config_hash → Full UPSERT if changed, update last_heartbeat only if same
Shutdown → ServiceDeregisteredEvent → status = DEREGISTERED
Stale detection (5min) → Manager sweep → status = UNHEALTHY
```

> Event type definitions and details → [Event & Registration Flow Details](BEP-1046/event-registration.md)

### Multi-Agent Considerations

In Agent's multi-agent mode (PRIMARY + AUXILIARY), SD registers only one entry per process. Uses the PRIMARY agent's `agent_id` as `instance_id`, and AUXILIARY agents continue using the existing `AgentHeartbeatEvent` → `agents` table path. Multi-agent is treated as a sub-concept of SD, with minimal integration in the current scope.

## Migration / Compatibility

### Backward Compatibility

- Existing `ServiceDiscoveryLoop` is not removed immediately; marked as deprecated
- Falls back to existing SD method when `[service-discovery]` config section is absent
- `config migrate service-discovery` CLI supports migration of existing deployments

### Breaking Changes

- New DB tables added (Alembic migration required)
- EventProducer added to Webserver (no impact on existing behavior)
- New value added to `EventDomain`

### Migration Steps

1. Create `service_catalog` and `service_catalog_endpoint` tables via Alembic migration
2. Generate `[service-discovery]` section in existing config files using `config migrate service-discovery` CLI
3. Restart services with new config → SD event publishing begins
4. Remove existing `ServiceDiscoveryLoop` as a separate task after all components are transitioned

### Future Extensibility

```
Current: Component → Redis Event → Manager (consumer) → DB
Future:  Component → Redis Event → SD Server (consumer) → DB
```

No changes required on the event publishing side (each component).

## Implementation Plan

### Phase 1: Common Foundation (BA-4315)

1. Add `ServiceDiscoveryConfig`, `ServiceEndpointConfig` Pydantic models
2. Add `[service-discovery]` section to each component's unified config
3. Define `ServiceRegisteredEvent`, `ServiceDeregisteredEvent` event types
4. Add `EventDomain.SERVICE_DISCOVERY`
5. `service_catalog`, `service_catalog_endpoint` DB models + Alembic migration
6. Update `generate-sample` command

### Phase 2: CLI Migration (BA-4316)

1. Define `MappingRule` data structure
2. Write per-component mapping rules (Agent, Manager, Storage, AppProxy)
3. Implement `config migrate service-discovery` CLI command
4. Unit tests for mapping rules

### Phase 3: Runtime Integration (BA-4317)

1. Add SD event publishing logic to each component (startup, heartbeat, shutdown)
2. Add EventProducer to Webserver
3. Implement SD event handler in Manager (DB upsert)
4. Implement Manager background sweep (mark stale services as UNHEALTHY)
5. Implement GraphQL query API
6. Mark `ServiceDiscoveryLoop` as deprecated

### Phase 4: Client Pool (BA-4318)

1. Implement `ServiceCatalogCache` (in-memory cache + self-preservation)
2. Implement `SDClientPool` (role/scope based endpoint selection)
3. Transition Manager's Storage Proxy client to SD-based
4. Transition Manager's AppProxy client to SD-based
5. Transition `AgentClientPool` address resolution to SD-based

## Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| 2026-02-07 | Adopt Redis Event → DB architecture | Reuse existing event infrastructure + SQL queryability | Direct DB polling (latency), etcd watch (complexity) |
| 2026-02-07 | role + scope 2D endpoint model | Express role and network scope independently | Single name field (ambiguous), role-only (no network distinction) |
| 2026-02-07 | Config-driven endpoint registration | Explicit, auditable, enables CLI migration tool | Code-based auto-inference (implicit), hybrid (complex) |
| 2026-02-07 | Self-preservation (Eureka pattern) | Preserve existing connections on backend failure, prevent cascading failures | Immediate eviction (cascading failure risk), TTL-only (inflexible) |
| 2026-02-07 | Remove host from scope → cluster/container/public | localhost included in cluster; standalone host scope unnecessary | Keep host (over-segmentation) |
| 2026-02-07 | Agent SD: one entry per process | Multi-agent is sub-concept; minimize complexity | Register each auxiliary (excessive, duplicates existing heartbeat) |
| 2026-02-07 | instance_id: SD config first + component fallback | Consistent priority rules across all components | Per-component separate rules (inconsistent), fixed UUID (file management overhead) |
| 2026-02-07 | Webserver: add EventProducer only | SD registration needed but event consumption (Dispatcher) unnecessary | Full event system adoption (excessive) |

## Open Questions

1. **Heartbeat DB load optimization**
   - Designed to only update `last_heartbeat` when `config_hash` is unchanged
   - Monitoring needed if service count grows very large

2. **Relationship with existing Agent heartbeat**
   - `AgentHeartbeatEvent` contains large data (resource slots, image lists, etc.)
   - Likely appropriate to keep separate from SD since purposes differ, but final decision needed after reviewing existing integration structures (AgentRow, scaling_group, etc.)

3. **AppProxy Coordinator to scaling_group mapping**
   - Currently `wsproxy_addr`/`wsproxy_api_token` stored in `scaling_groups` row
   - Need to decide: labels-based mapping vs separate junction table when transitioning to SD catalog

### Resolved Items

- **Webserver EventProducer**: Add Redis Stream connection + EventProducer only. EventDispatcher (event consumption) remains Manager-only
- **Scope query method**: Registration is config-based with explicit per-scope endpoint declaration. Queries filter by specifying desired scope

## References

- [BEP-1024: Agent RPC Connection Pooling](BEP-1024-agent-rpc-connection-pooling.md) — existing client pool patterns
- [BEP-1023: Unified Config Consolidation](BEP-1023-unified-config-consolidation.md) — config structure reference
- HashiCorp Consul — Catalog API, agent cache, blocking queries, anti-entropy
- Netflix Eureka — Client-side registry cache, self-preservation mode
- Kubernetes — EndpointSlices, kube-proxy iptables rules persistence
- Apache ZooKeeper — Ephemeral nodes, Curator ServiceCache
