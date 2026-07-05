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

Backend.AI serves models through a stack of concepts: a **deployment
endpoint** (`EndpointRow`) with autoscaling and a deployment strategy
(rolling / blue-green, BEP-1006/1049); one or more **replica groups**
(`ReplicaGroupRow`) within that endpoint — a primary group serving traffic
plus, mid-rollout, a target group being promoted — each owning its own
revision pointer, desired replica count, and `traffic_weight`; the backing
**replica sessions** (`RoutingRow`), each reachable at a
`kernel_host:kernel_port` and belonging to exactly one replica group; and an
AppProxy **circuit** that binds the endpoint to its replica sessions on a
proxy worker. (Circuit-level weighting is covered in detail, including its
current limits, in "Replica groups and traffic weight today" below.)

Today each endpoint is published at its *own* frontend slot — a dedicated
wildcard subdomain or port — with its own per-endpoint JWT, the *deployment
access token* (`EndpointTokenRow`). That shape is transparent and simple,
but it leaves a gap for LLM inference at the cluster level:

- **No single surface.** Every deployment has a different base URL. Clients
  cannot hold one address and pick a model by name, the way every
  OpenAI-compatible SDK expects.
- **No model abstraction.** Users address a *deployment*, not a *model*.
  There is no first-class way to publish one model name backed by several
  deployment endpoints — for A/B testing two revisions, or for balancing one
  model across resource groups.
- **No key governance.** A deployment access token grants access to one
  deployment; there is no API-key surface that scopes *which models* a
  consumer may see and use across the cluster.
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

### Deployment access tokens

The Manager mints per-endpoint JWTs via the coordinator
(`POST /v2/endpoints/{endpoint_id}/token` →
`Circuit.generate_jwt()`, HS256 with the cluster-wide `jwt_secret`), stores
them in `EndpointTokenRow`, and the stock worker verifies the bearer per
circuit. This is the deployment API's *access token*
(`create_access_token` in `services/deployment/service.py`); it grants
access to exactly one deployment.

### Coordinator → worker propagation

Two mechanisms exist (`src/ai/backend/appproxy/coordinator/types.py:CircuitManager`):

- **Legacy (aiohttp worker) mode.** Circuit changes are broadcast as Redis
  Pub/Sub events carrying the **full per-entity state**
  (`AppProxyCircuitCreatedEvent` / `…RouteUpdatedEvent` / `…RemovedEvent`).
  Circuit creation blocks up to 15 s for the **first** worker ack
  (`initialize_legacy_circuit`, raising `E10001` on timeout); route updates
  and removals are fire-and-forget. The worker pulls the circuit snapshot
  exactly once, at startup (`src/ai/backend/appproxy/worker/server.py:worker_registration_ctx`).
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

### Replica groups and traffic weight today

An endpoint's replicas are not a flat pool: they are partitioned into one or
more **replica groups** (`ReplicaGroupRow`), each owning a revision pointer,
a desired replica count, a `lifecycle` (ROLLING/STABLE/FAILED/DRAINING/DRAINED),
and a `traffic_weight` (0–100). `EndpointRow.primary_replica_group_id` is the
group serving traffic; `target_replica_group_id` is set only mid-rollout,
pointing at the group being promoted (reused in place for rolling updates,
freshly created for blue-green/canary). Every route (`RoutingRow`) belongs to
exactly one group via `replica_group_id`. The Manager's deployment-strategy
handler (`sokovan/deployment/handlers/deploying_promoting.py`) ramps the
target group's `traffic_weight` toward 100 (mirroring it down on the primary)
as promotion proceeds, per BEP-1049.

**This weight does not currently reach AppProxy.** `traffic_weight` is written
by the promoting/finalizing handlers and read back only as an FSM completion
gate — no code path propagates it to the coordinator. The wire type the
Manager actually pushes per route, `RouteEntry`
(`common/dto/appproxy_coordinator/v2/endpoint/types.py`), carries only
`session_id`, `route_id`, `kernel_host`, `kernel_port` — no weight field
exists on it today. The only traffic control that *does* reach the proxy is
coarser: a route's `traffic_status` (ACTIVE/INACTIVE) gates whether it is
included in a circuit's `route_info` at all (see `BEP-1049/blue-green.md`).
Gradual, weighted traffic shifting across replica groups was scoped out
explicitly when replica groups were introduced (PR #11871, "Follow-ups (out
of scope): Group-level traffic distribution via `traffic_weight`") and
remains open.

This proposal's `ratio` (§3, §7) is deliberately defined at **endpoint**
granularity so it composes cleanly once replica-group weight propagation
lands, but ROUTER-mode traffic during an in-flight rollout is, today,
unweighted across whichever routes are ACTIVE regardless of which replica
group they belong to. See "Weight composition and normalization" below and
the follow-up filed on
[continuum-router#804](https://github.com/lablup/continuum-router/issues/804).

## Proposed Design

### Terminology

This proposal introduces a second inference credential next to an existing,
customer-visible one. To avoid confusion, the two are named as follows and
used consistently throughout:

- **Deployment access token** — the *existing* credential: a per-deployment
  JWT minted via the coordinator and stored in `EndpointTokenRow` (the
  deployment API's "access token"). **It is neither renamed nor changed by
  this proposal** and keeps working for WILDCARD/PORT frontends exactly as
  today.
- **Model API key** — the *new* credential: an opaque `sk-…`-style key
  generated by the Manager, carrying an explicit, RBAC-validated allowed-model
  set, and presented to the ROUTER-mode worker the way any OpenAI-compatible
  SDK expects an API key. Custody is hash-only (§9).
- **Model publication** (or just *publication*) — the *new* first-class entity
  that makes a deployment reachable by model name through a router. One
  publication binds **a primary model name (plus optional aliases)** to **one
  or more deployment endpoints** (each with a split `ratio`) on **one router
  authority**, and carries a `control_mode`. It is the object users
  create/edit/delete; it is stored Manager-side (source of truth) and mirrored
  into the coordinator's `router_models` table. "Publish a model" = create a
  publication; "unpublish" = delete it. A publication is *not* a deployment and
  *not* a circuit — it is the **name-to-endpoint(s) binding** layered on top of
  them.
- **Model name** and **alias** — the **primary model name** is a publication's
  stable identifier and API path key (`/v2/routers/{authority}/models/{model}`);
  an **alias** is any *additional* name on the same publication that routes
  **identically** to the same endpoints. Aliases let one deployment be exposed
  under several names (e.g. `gpt-4` and `gpt-4-internal`). Every name (primary or
  alias) is unique within an authority and is **gated independently** for
  visibility — a key may surface one name but not another (§7). Aliases here are
  a *published* concept, distinct from any router-local alias config.
- **Authority** — the logical identity of a router (`Worker.authority`); HA
  replicas of one router share it. Publications and keys are scoped per
  authority. A **node** is one router *process* under an authority, identified
  by an ephemeral `node_id` for per-node liveness (§2a).
- **Replica group** — an *existing* Backend.AI concept this proposal composes
  with rather than introduces: a versioned sub-fleet of routes within one
  deployment endpoint (`ReplicaGroupRow`), each owning a revision pointer, a
  desired replica count, and a `traffic_weight`. An endpoint has a primary
  group (serving) and, mid-rollout, a target group (being promoted). A
  publication's `ratio` maps a model to **endpoints**, not to replica groups
  directly — see "Replica groups and traffic weight today" (Current Design)
  and §7.

Naming rationale: "access key" is deliberately avoided because it already
means the AK half of the platform keypair (`access_key`/`secret_key`);
"router … key" is avoided because it leaks a data-plane component name and
collides with the existing route/routing terminology of model serving
(`RoutingRow`, `route_info`). "Model API key" names the scope (models) and
matches what users already call the `sk-…` string they paste into an SDK.
Internal identifiers (the `router_api_keys` table, `/v2/routers/*` paths,
event names) may still reference the ROUTER frontend mode; only user-facing
surfaces (GraphQL/CLI/WebUI/docs) use the term *model API key*.

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
sessions via the circuit's `route_info`. An endpoint's own replicas are
internally partitioned into replica groups (primary + an optional mid-rollout
target group, see "Replica groups and traffic weight today"), but the worker
does not need to know that — see "Weight composition and normalization"
below for how the two levels the worker *does* see compose into a single
per-route weight. The Manager hands users the triple **(base URL, model
name, API key)** instead of a per-deployment URL.

#### Weight composition and normalization

`normalize(ratio × traffic_ratio)`, applied by flattening every candidate
replica across every mapped endpoint and normalizing once at the end, does
**not** reproduce the configured endpoint split when endpoints carry
different numbers of (or differently-weighted) replicas — flagged in review
on the paired continuum-router design
([PR #748, discussion](https://github.com/lablup/continuum-router/pull/748#discussion_r3465875781))
and still present in the shipped reconcile (`composed_weight` in
`src/appproxy/router/reconcile.rs`, continuum-router PR #817). The general
rule is: **normalize within a level before composing with the level above**,
so that a 7:3 `ratio` always yields a 7:3 traffic split regardless of how many
replicas back each side. Concretely, per-route weight should be:

```text
weight(route) = ratio(endpoint) × normalize_within_endpoint(
                   weight(route.replica_group) × traffic_ratio(route)
                )
```

where `weight(replica_group)` is the (currently unpropagated —
see above) `traffic_weight`, itself already normalized across an endpoint's
own replica groups by the promoting handler (primary + target sum to ~100).
This is a two-part fix, tracked in two places:

- **Endpoint-level normalization** (this proposal / continuum-router): the
  flatten-then-multiply bug applies regardless of replica groups and should
  be fixed in the router reconcile independent of anything else — filed as a
  design note on
  [continuum-router#804](https://github.com/lablup/continuum-router/issues/804).
- **Replica-group-level propagation** (Manager, tracked separately): until
  `traffic_weight` is composed into what the Manager pushes per route (the
  BA-6233 follow-up), the formula above degrades to
  `ratio × normalize_within_endpoint(traffic_ratio)` — correct for a stable
  endpoint, but blind to in-flight rollout progress.

### Request path and responsibility split

An LLM inference request resolves through three mapping layers, each owned
by a different part of the stack:

```text
API key ──(1: visibility)──► model ──(2: publication)──► endpoint(s) ──(3: replicas)──► replica session
        enforced by the router      defined in the Manager,           maintained by the core
        at request time             delivered via the coordinator     (autoscaling, health checks)
```

1. **key → models** (router). The router authenticates the key and restricts
   model listing and use to the key's allowed-model set. The router only
   *enforces* a materialized list; it never evaluates permissions itself.
2. **model → endpoints** (AppProxy). The publication mapping — which
   deployment endpoints serve a model, with what split ratios — is stored on
   the coordinator and pushed to the router as described below.
3. **endpoint → replica sessions** (core). Each endpoint's replica set is
   the circuit's `route_info`, fed from the Manager's `RoutingRow` state and
   flowing to the router through the existing circuit route-update events.
   Internally these replicas are partitioned into replica groups (primary +
   an optional mid-rollout target, owned by BEP-1049's deployment-strategy
   handler); that partitioning is not yet visible past the Manager (see
   "Replica groups and traffic weight today").

The layers split cleanly between what a **user configures deliberately** and
what the **system maintains continuously**:

| Mapping layer | Owner | How |
|---|---|---|
| Key generation / issuance | **User** | An explicit action via WebUI / API / CLI; the Manager mints the model API key and persists it with its owner. |
| Model → endpoint mapping | **User** | Explicit publication management via WebUI / API / CLI: choose the model name, the backing endpoints, and the split ratios (A/B tests, resource-group balancing). |
| Key → model visibility | **User at issuance, System for shrink** | `allowed_models` is an **explicit set chosen at issuance**, validated by the Manager to be ⊆ the owner's RBAC-visible published names (no privilege escalation). It is then **static except for two automatic shrink triggers**: publication-delete / endpoint-destroy (immediate) and owner-loses-RBAC-access (periodic reconcile). It **never auto-expands** — widening is an explicit re-issue. |
| Endpoint → replica sessions | **System** | Continuously updated by deployment scaling and health checks: `RoutingRow` changes flow to circuit `route_info` and on to the router as route-update events, with no user action. |

In other words, users decide *what is published, who gets a key, and which
models that key grants*; the system keeps *what actually serves the traffic*
correct continuously, and **automatically narrows** a key when the ground
beneath it disappears (a model is unpublished) or the owner loses access. The
router still only ever *enforces* a materialized `allowed_models` list — it
never evaluates permissions. The Manager keeps that list correct via two
bounded triggers rather than recomputing on every RBAC change:

- **Publication-delete / endpoint-destroy → immediate.** These are Manager
  mutations the Manager owns, so it prunes the affected names from every
  referencing key and pushes the update at once.
- **Owner loses RBAC access → periodic Manager reconciler.** The Manager has
  **no RBAC-change events to hook** (RBAC mutations are silent DB writes), so a
  periodic reconciler (modelled on the sokovan reconciler) recomputes each
  active key's `allowed_models` against current RBAC ∩ published names and
  pushes **shrink** diffs via `PUT /v2/routers/{authority}/api-keys/{key_id}`.
  Key counts are small (keys are issued deliberately), so a full recompute on a
  modest interval is cheap.

This makes revocation **two-tier** (see §8): explicit key revocation is fast;
RBAC-driven implicit revocation is bounded by the Manager reconcile interval
plus the worker's, and operators who need instant offboarding use the explicit
`DELETE` path.

### 1. Common: `FrontendMode.ROUTER`

```python
class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
    ROUTER = "router"  # new
```

`WorkerRequestModel` gains two optional fields:

```python
traffic_port: int | None  # ROUTER mode: advertised data-plane port
                          # (an LB may front the worker); defaults to api_port
node_id: str | None       # stable-per-process identity for per-node liveness
                          # (§2a); optional, also sent on each heartbeat
```

Registration validation per mode: ROUTER requires neither `port_range` nor
`wildcard_domain` (both must be null) and accepts `traffic_port`;
the existing modes are unchanged.

`node_id` is mode-independent: an ephemeral UUID a worker process generates
at startup and repeats on every registration and heartbeat. It is **optional**
and, when present, switches the authority to per-node liveness tracking (§2a);
when absent the legacy `nodes` counter path is used unchanged. ROUTER workers
send it from the start; the stock worker types are expected to adopt it in a
follow-up.

### 2. Coordinator: slot-free circuits

- `Worker._calculate_available_slots()` returns unbounded (`-1`) for ROUTER
  workers; `occupied_slots` accounting is skipped.
- `pick_worker()` treats a ROUTER worker as **unbounded capacity** (the same
  way it already treats `WILDCARD_DOMAIN`) so a ROUTER worker is a valid
  candidate for inference circuits. Without this, today's slot filter
  (`available_slots - occupied_slots > 0`) would exclude a ROUTER worker,
  whose slot count is `-1`.
- `add_circuit()` skips subdomain/port allocation: ROUTER circuits are
  created with `port = None` **and** `subdomain = None`.
- `Circuit.get_endpoint_url()` gains a ROUTER branch returning the worker's
  single advertised base URL (`hostname` + `traffic_port`, scheme from
  `tls_advertised`) — the same URL for every circuit on that worker.
- `open_to_public` is ignored for ROUTER circuits (API keys gate access);
  `allowed_client_ips` is still honoured by the worker.

#### Endpoint placement: how a circuit lands on a ROUTER worker

An endpoint's inference circuit reaches a ROUTER worker through the **existing
scaling-group routing**, not a new mechanism:

- A scaling group selects its AppProxy **coordinator** via
  `ScalingGroupProxyTarget` (scaling group → coordinator `addr` + `api_token`).
  Point **every** scaling group whose deployments should sit behind one model
  surface at the **same** coordinator — the one hosting the ROUTER authority.
  This is what lets a single router serve **multiple scaling groups** (the
  primary "one endpoint for many deployments across scaling groups" use case).
- Within that coordinator, workers are distinguished only by `protocol` and
  `accepted_traffics`. The ROUTER worker is the inference/HTTP worker; with the
  unbounded-slot treatment above, `pick_worker()` selects it for inference
  circuits.
- **Operational constraint (documented, not enforced):** do **not** colocate a
  stock inference worker (WILDCARD/PORT) with a ROUTER worker on the same
  coordinator. `pick_worker()` prefers wildcard, and there is no realistic key
  to separate them (the legacy `WorkerAppFilter` mechanism keys off
  domain/project/user/runtime_variant, never the scaling group, and is unused
  in practice). A ROUTER coordinator **may** still host *interactive* stock
  workers — `accepted_traffics` separates `inference` from `interactive`
  cleanly.

Consequence for publications: an endpoint can only be published on the
authority whose coordinator hosts its circuit, so a single publication spans
exactly the endpoints reachable on one authority (see §7 and the per-authority
scoping decision).

#### High availability

Multiple router nodes register under one `authority`, typically behind an
external L4 LB/VIP whose address is the advertised `hostname`. The coordinator
delivers the same circuits and mappings to every node of the authority, and
**HA synchronization is inherent in the shared-authority model — there is no
separate cross-node sync subsystem**: all nodes share one Worker row, Pub/Sub
events fan out to every node (filtered by `target_worker_authority`), and the
authority-scoped pull snapshot reconciles each node to identical desired
state. A late-joining or restarted node catches up via the full pull on
(re-)registration. Per-node identity and liveness are covered in §2a.

### 2a. Coordinator: per-node liveness

The shared-authority row makes the coordinator blind to individual nodes: a
crashed node never decrements `nodes` (only a graceful `DELETE` does), so the
counter drifts and the coordinator cannot expose per-node health. ROUTER mode
makes multi-node-per-authority the common case, so this proposal adds per-node
liveness. **This is a general coordinator capability** — wildcard/port workers
can be HA too — but ROUTER mode is what motivates introducing it here.

- **Identity.** A worker process sends an ephemeral `node_id` (§1) on
  registration and every heartbeat. It is not persisted by the worker; a
  restart yields a new `node_id` and the old one expires.
- **Liveness set as source of truth.** The coordinator keeps a per-authority
  liveness structure in `valkey_live` (member = `node_id`, value = `last_seen`),
  each entry TTL'd to the heartbeat timeout. A heartbeat upserts the node's
  entry; an expired entry means that node is gone.
- **`nodes` is derived, the counter retired.** When `node_id` is in use,
  `nodes = count(live entries)` and `status` flips to `LOST` only when the set
  empties — so a crash converges correctly without a graceful `DELETE`
  (deregistration becomes an optimization, not a correctness requirement).
- **Backward compatibility (dual-mode).** `node_id` is optional. Per authority,
  the first registration decides the mode: with `node_id` → liveness-set +
  derived `nodes`; without → the legacy `+1/−1` counter path, unchanged. Mixed
  modes within one authority do not occur because all nodes run the same build.
  Updating the stock worker types to send `node_id` is **follow-up work**.
- **Per-node metadata** captured at registration for the exposed view:
  `node_id`, the node's own direct address (each node may differ behind the
  VIP — useful for debugging), version, `registered_at`, `last_seen`.
- **Exposure.** The coordinator surfaces per-node health via REST
  (a `nodes: [...]` array on the worker-detail response, e.g.
  `GET /api/worker/{id}`) and via Prometheus metrics (live nodes per authority,
  heartbeat age per node). A Manager-side admin fleet view consumes this in the
  Manager surface phase (§7); the per-node `status` is *derived*
  (alive iff `last_seen` within timeout), not stored.

Responsibility split: the coordinator **observes** per-node health; the
**LB/VIP** is responsible for routing traffic away from dead nodes.

### 3. Coordinator: desired-state persistence

Two new tables, scoped per worker authority, with a per-authority monotonic
`revision` bumped in the same transaction as any mutation:

```text
router_models:
    id UUID PK
    worker_authority str  (indexed)
    model_name str        # primary name; the API/identity key for the publication
    aliases JSONB         # ["alias-a", …] additional names that route identically
    mappings JSONB        # [{"endpoint_id": UUID, "ratio": float}]
    control_mode str      # "manual" (user owns ratios) | "strategy-managed" (BEP-1049)
    created_at / updated_at
    UNIQUE (worker_authority, model_name)

router_api_keys:
    id UUID PK
    worker_authority str  (indexed)
    key_id str            # manager-side identifier
    token_hash str        # SHA-256 of the key material — never the plaintext (see Security)
    display_hint str      # masked tail for listings, e.g. "sk-…wxyz"
    allowed_models JSONB  # ["model-a", "alias-b"] — explicit per-name grant (primary or alias)
    expires_at datetime | None
    rate_limit int | None # per-node best-effort (§8); unit: requests/min
    created_at / updated_at
    UNIQUE (worker_authority, key_id)
```

Names are unique per authority: no name may appear as a `model_name` or in
any `aliases` of two different publications. The Manager (source of truth)
validates this at publish time; the coordinator does a best-effort check.
`ratio` is a non-negative **relative weight**, normalized per model across its
endpoints (need not sum to 1.0); `ratio = 0` drains an endpoint (mapped, no new
traffic). `control_mode` defaults to `manual`; `strategy-managed` hands ratio
ownership to the deployment-strategy handler (§7, BEP-1049) and rejects manual
ratio edits.

Persistence on the coordinator is required, not optional: the router
worker's runtime state is in-memory by design, so the coordinator must be
able to replay the full mapping/key set whenever a router node
(re-)registers. **Only the hash (`token_hash`) is persisted** — the plaintext
key is shown once at issuance and stored nowhere (see §9).

### 4. Coordinator: manager-scope REST API (new)

Authenticated with the shared `X-BackendAI-Token`, like the existing
`/v2/endpoints` family:

| Method & path | Purpose |
|---|---|
| `GET /v2/routers/{authority}/models` | list model mappings |
| `PUT /v2/routers/{authority}/models/{model}` | upsert: `{aliases, mappings: [{endpoint_id, ratio}], control_mode}` |
| `DELETE /v2/routers/{authority}/models/{model}` | unpublish a model (and all its aliases) |
| `GET /v2/routers/{authority}/api-keys` | list keys (masked via `display_hint`) |
| `PUT /v2/routers/{authority}/api-keys/{key_id}` | upsert: `{token_hash, allowed_models, expires_at, rate_limit}` |
| `DELETE /v2/routers/{authority}/api-keys/{key_id}?strict={bool}` | revoke a key (`strict` waits for all-live-nodes ack) |

The Manager passes the SHA-256 `token_hash`, never the plaintext, on the
api-keys upsert (the Manager hashes the freshly minted key and shows the
plaintext to the user once; see §7, §9). `strict` on delete (default `false`)
selects the all-live-nodes confirmation mode described below.

**Proactive-deploy semantics.** Each mutating call (1) persists to
PostgreSQL and bumps the authority's `revision`, (2) broadcasts the
corresponding event (below), (3) waits up to 15 s for the **first** worker
ack — the same pattern `initialize_legacy_circuit` uses — and returns. It
never waits for every node, and replica-session health never gates it. On
ack timeout the call still **succeeds** (the persisted state is
authoritative; pull reconciliation guarantees convergence) with the response
flagging propagation as deferred.

**Strict revocation (opt-in).** `DELETE …/api-keys/{key_id}?strict=true`
waits instead for an ack from **every currently-live node** (the per-node
liveness set from §2a), bounded by a timeout. On timeout it returns the set of
**unconfirmed nodes** so the operator can act (e.g. drain them at the LB)
rather than silently assuming convergence. This is enabled by per-node
liveness and the `node_id`-tagged ack event (§6); it tightens the control-plane
revocation window to all-nodes-applied but is not a hard real-time guarantee
(in-flight requests and LB timing remain).

### 5. Coordinator: worker-scope snapshot endpoint (new)

```text
GET /api/worker/{worker_id}/router-config?known_revision={r}
→ 304 Not Modified                         (empty body, if r == current revision)
→ 200 {revision, models: [...], api_keys: [...]}   (full snapshot, otherwise)
```

The router worker pulls this at registration (full in-memory state restore)
and on its reconcile timer, reconciling by **set-diff** — the same idiom as
`reconcile_traefik_etcd_state`, moved worker-side. A **single per-authority
`revision`** covers **both** `router_models` and `router_api_keys`, so a poll
returns the combined full state whenever anything changed and the worker
set-diffs the whole thing. The worker passes its last-applied revision via
`?known_revision=`; an unchanged revision yields a cheap `304`. (An explicit
query param is used rather than HTTP `ETag`/`If-None-Match` because the
coordinator's existing REST endpoints do not use conditional-GET middleware.)
The snapshot carries only `token_hash` values, never plaintext (§9); a key
change bumps the revision, which is what makes the worker pull the new hash.

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
| `appproxy_worker_router_config_applied_event` | ← worker (ack) | `(authority, node_id, kind, id)` — `node_id` attributes the ack to a node (§2a) so strict revocation (§4) can count per-node acks |

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

- **Model publications.** A new entity mapping a published model name —
  **plus optional aliases** (one deployment exposed under several names, all
  routing identically) — to one or more deployment endpoints with split
  ratios, targeted at **one** router authority. Exposed via GraphQL
  mutations/queries, CLI, and WebUI. The Manager validates that each
  `endpoint_id` exists and resolves to the target authority's coordinator
  (the coordinator stays permissive; the worker holds a mapping until its
  circuit arrives), and that all names are unique within the authority.
  `control_mode` defaults to `manual`. Endpoint lifecycle integration:
  destroying an endpoint removes it from any publication; if that empties the
  publication, the model stays published-but-empty (degrades to fallback /
  unavailable) and the Manager **warns** — it does **not** auto-unpublish.
- **Per-authority scope & discovery.** A publication targets one authority.
  Operators do **not** hand-type authority strings: the Manager discovers
  router authorities via a new `list_workers()` on the appproxy client
  (over the coordinators it already knows from `ScalingGroupProxyTarget`),
  filtering `frontend_mode == router`, and presents the set for targeting.
  The same call feeds the **router-fleet admin view** (per-node health, §2a).
  Publishing one model name across multiple authorities (e.g. multi-region) is
  **caller-side composition** — optionally a UI "apply to these N authorities"
  fan-out to N independent per-authority operations — not a multi-target
  entity.
- **Model API keys (hash-only custody).** Issuance is a user-initiated action
  (WebUI / API / CLI). The Manager mints an opaque `sk-…`-style token,
  **shows the plaintext to the user exactly once**, and persists only its
  `SHA-256` hash (+ a masked display hint) with the owning user/project and
  expiry — the deployment access token pattern lifted from endpoint scope to
  model scope, hardened to store no recoverable secret. It pushes only the
  hash to the coordinator (§4). **Rotation** is an atomic hash replacement
  (no dual-valid window; a brief old-still-valid tail bounded by propagation);
  zero-downtime overlap is achieved by issuing a second `key_id` and revoking
  the first. Issuing, listing (masked), rotating, and revoking are Manager
  operations.
- **Explicit, RBAC-validated, shrink-only visibility.** `allowed_models` is an
  explicit set the issuer chooses (per name — primary or alias), validated
  ⊆ the owner's RBAC-visible published names; thereafter static except for the
  two automatic shrink triggers (see "Request path and responsibility split").
  `/v1/models` for a key returns `allowed_models ∩ currently-published-names`,
  so aliases are independently gated and never auto-exposed.
- **Propagation.** The Manager never talks to a router directly; it calls
  the coordinator's `/v2/routers/*` API
  (`manager/clients/appproxy/client.py` gains the corresponding methods,
  including `list_workers()`), which persists and broadcasts as described
  above.
- **Deployment-strategy integration (BEP-1049).** `/v2/routers/*` is the shared
  ratio-control surface. A publication's `control_mode` selects the writer:
  `manual` (user owns ratios) or `strategy-managed` (the deployment-strategy
  handler owns ratios via the same API; manual ratio edits are rejected). This
  proposal adds the flag to avoid a dual-writer conflict; the canary/ramp
  mechanics are deferred to BEP-1049. Note this is a **coarser** axis than
  BEP-1049's own rollout mechanism: `control_mode` governs the publication's
  per-*endpoint* `ratio` (e.g. splitting traffic across two distinct
  `EndpointRow`s for a cross-endpoint canary), whereas BEP-1049's handler
  today ramps `traffic_weight` **within** one endpoint, across its replica
  groups — a mechanism this proposal does not touch and which does not
  currently reach `/v2/routers/*` at all (see "Replica groups and traffic
  weight today"). A `strategy-managed` writer that reflects intra-endpoint
  rollout progress into the publication's ratio has no data to draw from
  until that propagation exists.
- **Access info contract.** For deployments attached to a ROUTER
  publication, the user-visible access information becomes
  (gateway base URL, model name, model API key) instead of a per-deployment
  URL + deployment access token.

### 8. Failure model

| Failure | Outcome |
|---|---|
| Redis down | Events lost; manager call succeeds with ack timeout flagged; workers converge via periodic snapshot pull (`reconcile_interval`) |
| Worker node down during a change | Full replay via snapshot pull on re-registration |
| Coordinator cannot dial a worker (NAT/k8s) | Non-issue — the protocol never dials workers |
| Both signals lost | Periodic set-diff pull heals within `reconcile_interval` |
| Coordinator restart mid-fan-out | Desired state is in PostgreSQL; pull reconciliation converges |

**Two-tier revocation.** Revocation latency depends on the trigger:

| Revocation kind | Path | Worst-case window |
|---|---|---|
| **Explicit key revoke** (`DELETE …/api-keys/{id}`) | immediate Manager→coordinator push + worker pickup | ~worker `reconcile_interval` (default 15 s on the Continuum Router side); `?strict=true` tightens to all-live-nodes-applied |
| **RBAC-driven implicit revoke** (owner loses access → model shrinks out of key) | Manager reconciler tick **+** coordinator push **+** worker pickup | Manager reconcile interval **+** worker `reconcile_interval` |

Operators who need instant offboarding use the explicit `DELETE` path, so the
slower RBAC-driven window is a convenience bound, not a security hole. A node
that misses a key-removal notification still converges at its next pull.

**Per-node best-effort rate limiting.** With HA, each node enforces a key's
`rate_limit` independently, so the effective cluster ceiling is
≈ `rate_limit × live_nodes`. It is a coarse abuse-control knob (unit:
requests/min), not a global quota; true cluster-global limiting (a shared
counter) is deferred to preserve the stateless-node property.

### 9. Security

- All control-plane REST (manager→coordinator, worker→coordinator) keeps the
  shared `X-BackendAI-Token` authentication.
- **Hash-only key custody (plain `SHA-256`).** Plaintext key material exists
  only transiently in the Manager at generation and is shown to the user
  **once**; it is stored **nowhere**. The Manager DB, the coordinator DB
  (`router_api_keys.token_hash`), the `router-config` snapshot, and router
  memory all hold **only the hash** (+ a masked display hint). The router
  authenticates by hashing the presented bearer and comparing. A leaked hash is
  **not bearer-equivalent** (SHA-256 is not invertible and the router hashes
  what the client presents), so a coordinator/Manager DB compromise leaks
  nothing usable. High key entropy (128+ bits) makes unsalted `SHA-256` safe;
  no per-key salt (it would break hash-keyed lookup) and no slow KDF. Hashes
  never transit Redis (key events are id-only, §6); the two HTTP hops still
  carry only hashes and should run over TLS or a trusted network; values are
  never logged and listings are masked.
- Deployment access tokens (`Circuit.generate_jwt` / `EndpointTokenRow`) are
  **not used** for ROUTER circuits; model API keys replace them as the
  data-plane credential. Existing deployment access tokens continue to work
  for WILDCARD/PORT circuits unchanged.

## Migration / Compatibility

### Backward compatibility

- All changes are additive: a new enum value, two new optional registration
  fields (`traffic_port`, `node_id`), new tables, new columns, new API routes,
  and new event types. Stock WILDCARD/PORT workers, existing circuits,
  deployment access tokens, and the Traefik path are untouched.
- The per-node liveness change is **dual-mode and gated by `node_id`** (§2a):
  authorities whose workers do not send `node_id` keep the legacy `nodes`
  counter unchanged, so stock workers are unaffected until they adopt `node_id`
  in follow-up work.
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

### Relationship to BEP-1005 (longer-term consolidation)

BEP-1005 proposes dissolving the Coordinator into the Manager entirely
(shared Redis/etcd, mandatory Manager↔Worker East-West reachability), for
reasons unrelated to model serving (interactive session/circuit lifecycle
sync, TCP idle timeout). This proposal instead **deepens** the
Manager/Coordinator split: new Coordinator-side tables (`router_models`,
`router_api_keys`), a new REST surface, new events, and a propagation model
(§4, §8) whose ack-timeout/pull-reconcile shape exists specifically *because*
the Coordinator is a separate, not-always-reachable process — the opposite
of BEP-1005's premise. The two are not contradictory (BEP-1005 is Draft, not
targeted, and predates model publications entirely) but they are not
demonstrated compatible either: if BEP-1005 ever proceeds, §3–§6 here would
need to either migrate into the Manager or be re-justified once Manager
*is* the coordinator. Flagged here as an open question rather than resolved,
since it does not block this proposal's phases.

## Implementation Plan

1. **Phase 1 — common + coordinator core**: `FrontendMode.ROUTER`,
   `traffic_port`, `node_id`, registration validation, `pick_worker()`
   unbounded-ROUTER treatment (placement), slot-skipping `add_circuit()`,
   `get_endpoint_url()` ROUTER branch.
2. **Phase 1a — per-node liveness**: `valkey_live` liveness set + TTL eviction,
   `nodes` derived (dual-mode by `node_id` presence), per-node metadata, the
   `nodes: [...]` exposure on worker-detail REST + Prometheus metrics.
3. **Phase 2 — desired state + APIs**: `router_models` (with `aliases`,
   `control_mode`) / `router_api_keys` (with `token_hash`, `display_hint`)
   tables (+ alembic migration for the appproxy DB), per-authority `revision`,
   `/v2/routers/*` manager-scope API, `/api/worker/{id}/router-config`
   worker-scope snapshot with `?known_revision=` conditional polling.
4. **Phase 3 — propagation**: the five events (ack carrying `node_id`),
   first-ack proactive-deploy wiring, opt-in strict all-live-nodes revocation,
   replay-on-registration.
5. **Phase 4 — manager surface**: model publication (with aliases,
   `control_mode`) + model API key entities (hash-only custody, atomic
   rotation), explicit RBAC-validated shrink-only visibility + the periodic
   shrink reconciler, GraphQL/CLI, appproxy client methods (incl.
   `list_workers()` for authority discovery + fleet view), endpoint lifecycle
   hooks (prune + empty-publication warning), WebUI access-info presentation.
6. **Phase 5 — end-to-end validation**: integration tests against a
   Continuum Router worker built with its `appproxy` feature (worker-side
   tracking: lablup/continuum-router#748 and its implementation epic).

## Resolved Decisions

The four questions originally open here were resolved in a design review
(2026-06-21):

- **Authority scoping granularity → per-authority, caller-side composition.**
  A publication targets one authority. The "single surface across scaling
  groups" goal is met by routing several scaling groups to one coordinator
  (§2); cross-authority (e.g. multi-region) is an optional Manager UI fan-out
  to N independent per-authority operations, not a multi-target entity (§7).
- **Key custody hardening → hash-only (plain `SHA-256`).** Plaintext is shown
  once at issuance and stored nowhere; Manager/coordinator/router hold only the
  hash. Replay works with hashes; a leaked hash is not bearer-equivalent (§9).
- **Strict revocation → default first-ack + opt-in all-live-nodes mode.**
  Enabled by per-node liveness (§2a) and the `node_id`-tagged ack (§6); strict
  `DELETE` returns unconfirmed nodes on timeout (§4). Revocation is two-tier
  (§8).
- **Autoscaling interplay → shared `/v2/routers/*` surface + `control_mode`.**
  A per-publication `manual`/`strategy-managed` flag prevents dual-writer
  conflict; canary/ramp mechanics are deferred to BEP-1049 (§7).

Remaining follow-ups (out of scope for this proposal):

- Updating stock WILDCARD/PORT worker types to send `node_id` so they gain
  per-node liveness (§2a dual-mode keeps them working until then).
- Cluster-global rate limiting via a shared counter, if per-node best-effort
  (§8) proves insufficient for some tenant.
- The BEP-1049 deployment-strategy ratio-control mechanics behind
  `control_mode = strategy-managed`.
- **Replica-group traffic-weight propagation** (Manager side, tracked as a
  BA-6233 follow-up): composing `ReplicaGroupRow.traffic_weight` into the
  per-route weight the Manager pushes to the coordinator, so an in-flight
  BEP-1049 rollout is reflected in ROUTER-mode traffic. See "Replica groups
  and traffic weight today" and "Weight composition and normalization."
- **Endpoint-level weight normalization** (continuum-router side): the
  flatten-then-multiply weight formula in the shipped reconcile does not
  reproduce the configured per-endpoint `ratio` when endpoints have uneven
  replica counts — flagged in review, not yet fixed; tracked on
  [continuum-router#804](https://github.com/lablup/continuum-router/issues/804).

## Future Directions

### Hierarchical (chained) routing instead of a flattened replica pool

The two gaps above (replica-group weight never reaching the data plane, and
endpoint-level weights not being normalized correctly) share a root cause:
today's model → replica mapping is **flattened to one level** — every
replica of every mapped endpoint sits in one weighted pool, so any
replica-count change anywhere recomputes weights for the whole model, and
`ratio` has to be composed with per-replica weight in a single formula
instead of being independently normalized at each level.

`BackendConfig` in continuum-router already supports this without any code
change: a backend's `url` is an arbitrary HTTP endpoint (`backend_type` is
already provider-agnostic — openai/anthropic/vllm/generic), not necessarily a
raw `kernel_host:kernel_port`. That means **a backend can itself be another
router/circuit's address** — nothing structural forces flattening down to
individual replicas.

**Proposed direction:** give the ROUTER-mode worker one `BackendConfig` per
*endpoint*, pointing at that endpoint's own existing WILDCARD/PORT circuit
URL (kept alive as internal-only plumbing, no longer user-facing) instead of
at that endpoint's individual replicas:

```text
today (flattened):      model → [replica₁, replica₂, …, replicaₙ]   (n changes constantly)
chained (hierarchical):  model → [endpoint_A, endpoint_B]            (changes only on (re)publish)
                                      │              │
                                      ▼              ▼
                               endpoint_A's    endpoint_B's
                               own circuit      own circuit
                               (existing per-endpoint LB — already
                                balances its own replicas/groups)
```

This makes the isolation property this section asks for **inherent** rather
than something the weight formula has to work around:

- The root weight table has one entry per endpoint in a publication — small
  and stable — so normalizing `ratio` across it trivially satisfies the
  jopemachine fix; there is no "endpoints with uneven replica counts"
  problem left at that level, because each endpoint contributes exactly one
  upstream regardless of its internal replica or replica-group count.
- Replica-count changes and BEP-1049 rollout ramps (`traffic_weight` between
  a primary and target replica group) are absorbed entirely by the
  endpoint's own existing circuit — no `router_models` mutation, no
  `revision` bump, no re-pull by every ROUTER node. Replica-group weight
  propagation (the open item above) would land in the existing per-circuit
  sync path, not in a new ROUTER-specific wire format.

**Trade-offs, not yet weighed against each other:** an added proxy hop per
request (likely small on an intra-cluster network, but unverified for
streaming responses specifically); every ROUTER-published endpoint needs to
keep a live circuit even though it's no longer the public surface, which
changes §2's "Endpoint placement" assumption that an endpoint's inference
circuit lands directly on the ROUTER worker; and health/failure detection
becomes per-endpoint-circuit rather than per-replica at the root, which may
be desirable (replica health is already that circuit's job) or may need
finer propagation depending on how it's implemented.

**Alternative achieving the same isolation without an extra hop:** teach
continuum-router's own selection algorithm to be two-tier internally — pick
an endpoint by `ratio`, then a replica within it by locally-normalized weight
— mirroring Envoy's weighted-cluster-of-clusters pattern. No dependency on a
live per-endpoint circuit, but requires a data-model/algorithm change inside
continuum-router rather than being achievable through topology alone.

Neither direction is committed here; both are recorded as design notes on
[continuum-router#804](https://github.com/lablup/continuum-router/issues/804)
for whoever picks up the normalization and replica-group-propagation
follow-ups.

## References

- [Continuum Router: AppProxy Worker Mode design](https://github.com/lablup/continuum-router/pull/748)
  (`docs/en/architecture/appproxy-worker.md`) — the worker-side half of this
  design: two-level routing realization, weight composition, key
  enforcement, and the worker's reconcile loop.
- [continuum-router#804](https://github.com/lablup/continuum-router/issues/804)
  — epic tracking the router-side ROUTER-mode implementation (now shipped);
  follow-up comment there tracks the weight-normalization and replica-group
  propagation gaps noted above.
- [BEP-1005: Unified AppProxy](BEP-1005-unified-appproxy.md) — longer-term
  consolidation direction; this proposal stays within the current
  coordinator/worker split and remains compatible with it.
- [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md),
  [BEP-1049: Deployment Strategy Handler](BEP-1049-deployment-strategy-handler.md)
  — deployment/replica lifecycle this proposal builds on.
- [BEP-1008: RBAC](BEP-1008-RBAC.md),
  [BEP-1012: RBAC](BEP-1012-RBAC.md),
  [BEP-1048: RBAC Entity-Relationship Model](BEP-1048-RBAC-entity-relationship-model.md)
  — the scope/permission model from which key→model visibility is derived.
- `src/ai/backend/appproxy/coordinator/types.py` (`CircuitManager`) — the
  existing propagation mechanisms whose idioms this proposal reuses.
