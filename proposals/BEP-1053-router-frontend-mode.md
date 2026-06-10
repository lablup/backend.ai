---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2026-06-10
Created-Version: 26.4.4
Target-Version:
Implemented-Version:
---

# ROUTER Frontend Mode: LLM Inference Gateway Integration

## Related Issues

- JIRA: TBD
- GitHub: [lablup/continuum-router#748](https://github.com/lablup/continuum-router/pull/748)
  (the worker-side design document this proposal pairs with:
  `docs/en/architecture/appproxy-worker.md`)

## Motivation

Backend.AI serves models through a stack of three concepts: a **deployment
endpoint** (`EndpointRow`) with replicas, revisions, and autoscaling; one or
more backing **replica sessions** (`RoutingRow`), each reachable at a
`kernel_host:kernel_port`; and an AppProxy **circuit** that binds the endpoint
to its replicas on a proxy worker, load balancing by `traffic_ratio`.

Today each endpoint is published at its *own* frontend slot — a dedicated
wildcard subdomain or port — with its own per-endpoint JWT token
(`EndpointTokenRow`). That shape is transparent and simple, but it leaves a
gap for LLM inference at the cluster level:

- **No single surface.** Every deployment has a different base URL. Clients
  cannot hold one address and pick a model by name, the way every
  OpenAI-compatible SDK expects.
- **No model abstraction.** Users address a *deployment*, not a *model*.
  There is no first-class way to publish one model name backed by several
  deployment endpoints — for A/B testing two revisions, or for balancing one
  model across resource groups.
- **No key governance.** Per-endpoint JWTs grant access to one deployment;
  there is no API-key surface that scopes *which models* a consumer may see
  and use across the cluster.
- **No LLM-aware data plane.** The stock worker forwards bytes. Protocol
  translation (OpenAI ↔ Anthropic ↔ Gemini), fallback chains, response
  caching, and prefix/KV-cache-aware routing all need an L7 router that
  understands inference traffic.

[Continuum Router](https://github.com/lablup/continuum-router) provides
exactly that data plane. This proposal adds the Backend.AI-side support to
run it as a new kind of AppProxy worker: a **ROUTER frontend mode** in which
the worker holds a **single binding address** for its sole endpoint, all slot
management is skipped, and the request's `model` name (gated by an API key)
becomes the addressing key. The AppProxy coordinator remains the control
plane; the Backend.AI Manager gains a management surface for
**key–model–service mappings** that define what the router publishes.

## Current Design

### Frontend modes and slots

`FrontendMode` (`src/ai/backend/appproxy/common/types.py`) has two values:

```python
class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
```

A worker advertises a slot space at registration (`wildcard_domain` or
`port_range`); the coordinator allocates one slot (a generated subdomain or a
port) per circuit in `add_circuit()`, and `Circuit.get_endpoint_url()` builds
a per-deployment URL from that slot. `Worker._calculate_available_slots()`
returns `-1` for wildcard and the range size for port mode.

### Inference access tokens

The Manager mints per-endpoint JWTs via the coordinator
(`POST /v2/endpoints/{endpoint_id}/token` →
`Circuit.generate_jwt()`, HS256 with the cluster-wide `jwt_secret`), stores
them in `EndpointTokenRow`, and the stock worker verifies the bearer per
circuit. A token grants access to exactly one deployment.

### Coordinator → worker propagation

Two mechanisms exist (`coordinator/types.py:CircuitManager`):

- **Legacy (aiohttp worker) mode.** Circuit changes are broadcast as Redis
  Pub/Sub events carrying the **full per-entity state**
  (`AppProxyCircuitCreatedEvent` / `…RouteUpdatedEvent` / `…RemovedEvent`).
  Circuit creation blocks up to 15 s for the **first** worker ack
  (`initialize_legacy_circuit`, raising `E10001` on timeout); route updates
  and removals are fire-and-forget. The worker pulls the circuit snapshot
  exactly once, at startup (`worker/server.py:worker_registration_ctx`).
- **Traefik mode.** The coordinator writes each circuit's full desired state
  into etcd (`atomic_replace_prefixes`) and a leader-elected
  `reconcile_traefik_routes` task re-publishes every circuit and drops
  orphans every 30 s — explicitly "a safety net against missed propagation
  events (e.g. on coordinator restart or transient Redis issues)".

Note the asymmetry this proposal will reuse: the protocol has **no
coordinator→worker dialing** (events + pull only), achieves idempotency via
**full-state-per-entity** payloads rather than version chains, and the newer
Traefik path compensates for lossy events with **periodic set-diff
reconciliation** against the desired state.

## Proposed Design

### Overview

```text
   Backend.AI Manager ──(key–model–service mappings)──► AppProxy Coordinator
        │  user creates deployments,                        │ persists desired state
        │  defines models & API keys                        │ (PostgreSQL); schedules
        ▼                                                   │ circuits; broadcasts
   deployment endpoints (replica sessions)                  │ events (Redis Pub/Sub)
                                                            ▼
   client ── POST /v1/chat/completions ──► continuum-router worker
             Authorization: Bearer <key>     (frontend_mode = router,
             {"model": "llama-4-chat", …}     one address, no slots)
                                                │
                                                ▼  weighted selection
                                       replica sessions (kernels)
```

Two-level hierarchical routing on the worker: an API key scopes the visible
**models**; a model maps to one or more **deployment endpoints** (each
mapping carrying a split `ratio`); each endpoint resolves to its replica
sessions via the circuit's `route_info`, weighted by
`ratio × traffic_ratio`. The Manager hands users the triple **(base URL,
model name, API key)** instead of a per-deployment URL.

### 1. Common: `FrontendMode.ROUTER`

```python
class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
    ROUTER = "router"  # new
```

`WorkerRequestModel` gains one optional field:

```python
traffic_port: int | None  # ROUTER mode: advertised data-plane port
                          # (an LB may front the worker); defaults to api_port
```

Registration validation per mode: ROUTER requires neither `port_range` nor
`wildcard_domain` (both must be null) and accepts `traffic_port`;
the existing modes are unchanged.

### 2. Coordinator: slot-free circuits

- `Worker._calculate_available_slots()` returns unbounded (`-1`) for ROUTER
  workers; `occupied_slots` accounting is skipped.
- `add_circuit()` skips subdomain/port allocation: ROUTER circuits are
  created with `port = None` **and** `subdomain = None`.
- `Circuit.get_endpoint_url()` gains a ROUTER branch returning the worker's
  single advertised base URL (`hostname` + `traffic_port`, scheme from
  `tls_advertised`) — the same URL for every circuit on that worker.
- `open_to_public` is ignored for ROUTER circuits (API keys gate access);
  `allowed_client_ips` is still honoured by the worker.
- HA: multiple router nodes register under one `authority` (the existing
  `nodes`-counter semantics), typically behind an external L4 LB whose
  address is the advertised `hostname`. The coordinator delivers the same
  circuits and mappings to every node of the authority.

### 3. Coordinator: desired-state persistence

Two new tables, scoped per worker authority, with a per-authority monotonic
`revision` bumped in the same transaction as any mutation:

```text
router_models:
    id UUID PK
    worker_authority str  (indexed)
    model_name str
    mappings JSONB        # [{"endpoint_id": UUID, "ratio": float}]
    created_at / updated_at
    UNIQUE (worker_authority, model_name)

router_api_keys:
    id UUID PK
    worker_authority str  (indexed)
    key_id str            # manager-side identifier
    token str             # opaque key material (see Security)
    allowed_models JSONB  # ["model-a", "model-b"]
    expires_at datetime | None
    rate_limit int | None
    created_at / updated_at
    UNIQUE (worker_authority, key_id)
```

Persistence on the coordinator is required, not optional: the router
worker's runtime state is in-memory by design, so the coordinator must be
able to replay the full mapping/key set whenever a router node
(re-)registers.

### 4. Coordinator: manager-scope REST API (new)

Authenticated with the shared `X-BackendAI-Token`, like the existing
`/v2/endpoints` family:

| Method & path | Purpose |
|---|---|
| `GET /v2/routers/{authority}/models` | list model mappings |
| `PUT /v2/routers/{authority}/models/{model}` | upsert: `{mappings: [{endpoint_id, ratio}]}` |
| `DELETE /v2/routers/{authority}/models/{model}` | unpublish a model |
| `GET /v2/routers/{authority}/api-keys` | list keys (masked) |
| `PUT /v2/routers/{authority}/api-keys/{key_id}` | upsert: `{token, allowed_models, expires_at, rate_limit}` |
| `DELETE /v2/routers/{authority}/api-keys/{key_id}` | revoke a key |

**Proactive-deploy semantics.** Each mutating call (1) persists to
PostgreSQL and bumps the authority's `revision`, (2) broadcasts the
corresponding event (below), (3) waits up to 15 s for the **first** worker
ack — the same pattern `initialize_legacy_circuit` uses — and returns. It
never waits for every node, and replica-session health never gates it. On
ack timeout the call still **succeeds** (the persisted state is
authoritative; pull reconciliation guarantees convergence) with the response
flagging propagation as deferred.

### 5. Coordinator: worker-scope snapshot endpoint (new)

```text
GET /api/worker/{worker_id}/router-config
→ {revision, models: [...], api_keys: [...]}
```

The router worker pulls this at registration (full in-memory state restore)
and on its reconcile timer, reconciling by **set-diff** — the same idiom as
`reconcile_traefik_etcd_state`, moved worker-side. The opaque `revision`
makes an unchanged poll a cheap no-op.

### 6. Coordinator: new Pub/Sub events

Five new events on the existing `events_all-appproxy` bus, following the
existing envelope and conventions (each inbound event carries the **full new
state of exactly one entity**, or its deletion — idempotent,
last-writer-wins, no version chain):

| Event | Direction | args |
|---|---|---|
| `appproxy_router_model_updated_event` | → worker | `(authority, model_json)` — full mapping state |
| `appproxy_router_model_removed_event` | → worker | `(authority, model_name)` |
| `appproxy_router_key_updated_event` | → worker | `(authority, key_id)` — **notification only, no token** |
| `appproxy_router_key_removed_event` | → worker | `(authority, key_id)` — applied immediately |
| `appproxy_worker_router_config_applied_event` | ← worker (ack) | `(authority, kind, id)` |

**Key material never rides the event bus.** Mapping events carry full
payloads (a mapping contains no secrets), but key events are id-only
notifications: the worker fetches key material via the authenticated
`router-config` snapshot. Circuit events already transit this shared bus but
carry kernel addresses, never credentials; this design preserves that
property.

The coordinator emits these events for ROUTER workers in **both**
coordinator modes — the Traefik/etcd path applies to stock circuits only and
never signals a ROUTER worker.

### 7. Manager: key–model–service mapping management

The Manager is the **source of truth and the single user-facing surface**:

- **Model publications.** A new entity mapping a published model name to one
  or more deployment endpoints with split ratios, targeted at a router
  authority. Exposed via GraphQL mutations/queries, CLI, and WebUI. Endpoint
  lifecycle integration: destroying an endpoint removes it from any
  publication (re-publishing the mapping minus that endpoint).
- **Router API keys.** Key material (an opaque `sk-…`-style token) is
  generated by the Manager and persisted with the owning user/project, the
  allowed model set, and expiry — the `EndpointTokenRow` pattern lifted from
  endpoint scope to model scope. Issuing, listing, rotating, and revoking
  are Manager operations.
- **Propagation.** The Manager never talks to a router directly; it calls
  the coordinator's `/v2/routers/*` API
  (`manager/clients/appproxy/client.py` gains the corresponding methods),
  which persists and broadcasts as described above.
- **Access info contract.** For deployments attached to a ROUTER
  publication, the user-visible access information becomes
  (router base URL, model name, API key) instead of a per-deployment URL +
  endpoint JWT.

### 8. Failure model

| Failure | Outcome |
|---|---|
| Redis down | Events lost; manager call succeeds with ack timeout flagged; workers converge via periodic snapshot pull (`reconcile_interval`) |
| Worker node down during a change | Full replay via snapshot pull on re-registration |
| Coordinator cannot dial a worker (NAT/k8s) | Non-issue — the protocol never dials workers |
| Both signals lost | Periodic set-diff pull heals within `reconcile_interval` |
| Coordinator restart mid-fan-out | Desired state is in PostgreSQL; pull reconciliation converges |

Bounded revocation: a node that misses a key-removal notification converges
at its next pull, so the worst-case revocation window on that node is the
worker's `reconcile_interval` (default 15 s on the Continuum Router side).

### 9. Security

- All control-plane REST (manager→coordinator, worker→coordinator) keeps the
  shared `X-BackendAI-Token` authentication.
- Key material is at rest in the Manager and the coordinator, in memory in
  the router, and never transits Redis. Both HTTP hops must run over TLS or
  a trusted network; key values must never be logged; listings are masked.
- Per-circuit JWTs (`Circuit.generate_jwt` / `EndpointTokenRow`) are **not
  used** for ROUTER circuits; router API keys replace them as the data-plane
  credential. Existing endpoint tokens continue to work for WILDCARD/PORT
  circuits unchanged.

## Migration / Compatibility

### Backward compatibility

- All changes are additive: a new enum value, a new optional registration
  field, new tables, new API routes, and new event types. Stock
  WILDCARD/PORT workers, existing circuits, endpoint tokens, and the Traefik
  path are untouched.
- A ROUTER worker cannot register against a coordinator that predates this
  proposal (registration validation rejects the unknown `frontend_mode`);
  this is the intended version gate.
- `SerializableCircuit` consumers must tolerate `frontend_mode == "router"`
  with both `port` and `subdomain` null; existing workers already filter
  events by `target_worker_authority`, so they never see ROUTER circuits.

### Breaking changes

None for existing deployments. The WebUI/CLI flows that display endpoint
URLs need a new presentation path for ROUTER-published deployments
(base URL + model name + key), which is additive.

## Implementation Plan

1. **Phase 1 — common + coordinator core**: `FrontendMode.ROUTER`,
   `traffic_port`, registration validation, slot-skipping `add_circuit()`,
   `get_endpoint_url()` ROUTER branch.
2. **Phase 2 — desired state + APIs**: `router_models` / `router_api_keys`
   tables (+ alembic migration for the appproxy DB), per-authority
   `revision`, `/v2/routers/*` manager-scope API,
   `/api/worker/{id}/router-config` worker-scope snapshot.
3. **Phase 3 — propagation**: the five events, first-ack proactive-deploy
   wiring in the mutation handlers, replay-on-registration.
4. **Phase 4 — manager surface**: model publication + router API key
   entities, GraphQL/CLI, appproxy client methods, endpoint lifecycle hooks,
   WebUI access-info presentation.
5. **Phase 5 — end-to-end validation**: integration tests against a
   Continuum Router worker built with its `appproxy` feature (worker-side
   tracking: lablup/continuum-router#748 and its implementation epic).

## Open Questions

- **Authority scoping granularity.** Mappings and keys are scoped per router
  authority. Should a publication be able to target multiple authorities
  (e.g. one per region) in a single Manager operation, or is that a
  composition concern left to the caller?
- **Key custody hardening.** The coordinator stores key material in
  plaintext to support replay. Should both Manager and coordinator store
  only an HMAC/hash with the plaintext shown once at issuance — at the cost
  of the router having to match hashes instead of values, or of re-issuing
  on every replay?
- **Strict revocation option.** Is the `reconcile_interval`-bounded
  revocation window acceptable for all tenants, or do we need an optional
  all-ALIVE-nodes confirmation mode for key deletion?
- **Autoscaling interplay.** Mapping ratios are static; should the
  deployment-strategy handler (BEP-1049) be able to adjust ratios
  dynamically (e.g. canary promotion) through the same `/v2/routers/*` API?

## References

- [Continuum Router: AppProxy Worker Mode design](https://github.com/lablup/continuum-router/pull/748)
  (`docs/en/architecture/appproxy-worker.md`) — the worker-side half of this
  design: two-level routing realization, weight composition, key
  enforcement, and the worker's reconcile loop.
- [BEP-1005: Unified AppProxy](BEP-1005-unified-appproxy.md) — longer-term
  consolidation direction; this proposal stays within the current
  coordinator/worker split and remains compatible with it.
- [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md),
  [BEP-1049: Deployment Strategy Handler](BEP-1049-deployment-strategy-handler.md)
  — deployment/replica lifecycle this proposal builds on.
- `src/ai/backend/appproxy/coordinator/types.py` (`CircuitManager`) — the
  existing propagation mechanisms whose idioms this proposal reuses.
