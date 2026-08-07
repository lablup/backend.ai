<!-- context-for-ai
type: detail-doc
parent: BEP-1053 (ROUTER Frontend Mode)
scope: Compatibility guarantees, version gates, and the operational procedure for adding a ROUTER surface to an existing AppProxy deployment (including the colocation fail-fast) with rollback.
depends-on: [coordinator.md]
key-decisions:
  - Fail-fast on stock/ROUTER inference-worker colocation (2026-07-15)
  - Mixed node_id adoption handled deterministically (2026-07-15)
-->

# BEP-1053: Migration and Compatibility

## Summary

All changes are additive; nothing breaks existing deployments. The one
operational constraint — a coordinator hosts either stock inference workers
or a ROUTER worker, never both — is enforced at registration with an
explicit error, and the procedure below shows how to introduce a ROUTER
surface next to an existing setup without touching it.

## Backward compatibility

- Additive changes only: a new enum value, two optional registration fields
  (`traffic_port`, `node_id`), optional circuit-payload fields
  (`replica_groups`, `replica_group_id`), new tables, new API routes, new
  event types. Stock WILDCARD/PORT workers, existing circuits, deployment
  access tokens, and the Traefik path are untouched.
- **Circuit payload additions are optional.** Stock workers tolerate unknown
  fields (existing serde/parse behaviour); routes without
  `replica_group_id` fall into an implicit default group (weight 100),
  reproducing today's group-blind balancing — so an older Manager works
  against a newer coordinator and router, minus rollout-weighted traffic.
- **Per-node liveness is mixed-adoption-safe**: `nodes` = liveness-set count
  + legacy counter (coordinator.md), so stock workers that do not yet send
  `node_id` keep working, including during a rolling upgrade that mixes old
  and new nodes under one authority.
- `SerializableCircuit` consumers must tolerate `frontend_mode == "router"`
  with both `port` and `subdomain` null; existing workers filter events by
  `target_worker_authority` and never see ROUTER circuits.

## Version gates

| Combination | Behaviour |
|---|---|
| ROUTER worker → older coordinator | Registration rejected (unknown `frontend_mode`) — the intended gate |
| Older Manager → newer coordinator | Works; no publications/keys until the Manager is upgraded; no group weights on routes |
| Newer Manager → older coordinator | `/v2/routers/*` calls fail explicitly; deployment serving unaffected |

## Adding a ROUTER surface to an existing AppProxy deployment

The colocation fail-fast (coordinator.md) means an existing coordinator that
already hosts stock **inference** workers cannot simply add a ROUTER worker —
the registration is rejected with an explicit error naming the conflict.
The supported path is a dedicated coordinator for the ROUTER authority:

1. **Upgrade** the shared components: coordinator (schema migration for
   `router_models` / `router_api_keys`, APIs, events) and Manager (its own
   schema migration + surfaces). No behaviour changes yet.
2. **Stand up the ROUTER coordinator** (a new coordinator instance, or an
   existing one hosting only *interactive* stock workers — those colocate
   freely).
3. **Register the router node(s)** under one authority (behind an L4 LB/VIP
   for HA), pointed at that coordinator and the event bus. Verify
   registration and per-node liveness in the fleet view.
4. **Route scaling groups.** Point each scaling group whose deployments
   should sit behind the surface at the ROUTER coordinator
   (`ScalingGroupProxyTarget`). New/rescheduled inference circuits from
   those scaling groups now land on the ROUTER worker. Deployments in
   scaling groups left untouched keep their stock workers and per-deployment
   URLs indefinitely.
5. **Publish models** for the target endpoints (fails fast if an endpoint's
   scaling group does not resolve to this coordinator) and **issue model API
   keys**; hand consumers the (base URL, model name, key) triple.
6. **Retire per-deployment presentation per policy** — e.g. stop displaying
   per-deployment URLs for published endpoints and let their deployment
   access tokens expire. Unpublished deployments are unaffected.

Rollback at any step deletes what the step created (publications, keys, the
router registration, the scaling-group repointing); steps 1–3 change no
serving behaviour at all.

## Breaking changes

None for existing deployments. The WebUI/CLI flows that display endpoint
URLs gain a new presentation path for ROUTER-published deployments
(base URL + model name + key), which is additive.
