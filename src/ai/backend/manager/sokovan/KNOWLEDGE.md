---
name: sokovan-coordinator-model
type: design-rationale
description: tick-based coordinator operating model (schedule, deployment, replica, idle check), handler vs coordinator responsibility split, replica-over-route terminology, declarative status_transitions rationale, reconcile/stages direction
scope: src/ai/backend/manager/sokovan
keywords: [coordinator, handler, tick, status_transitions, retry, reconcile]
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---
# Manager Sokovan layer — Knowledge

> For the rules, see `AGENTS.md` in the same directory. For detailed architecture, see `README.md` (and `scheduler/README.md`,
> `deployment/README.md`); for the design, see `proposals/BEP-1030` (status transitions) and `BEP-1033/*`.

## Operating model (tick-based coordinator)

The coordinators (Schedule / Deployment / Replica) run one tick periodically, querying entities in the target status and
passing them to the handlers. The idle checker (`idle_check/`) also lives in sokovan and follows the same tick model.

Terminology: prefer **replica** over "route" in new code and docs — the `route` naming
(e.g. `deployment/route/`) is the outgoing form of the same concept.

- **handler**: judges and returns only the result of its action (success / failure / skip, etc.).
- **coordinator**: takes on history-based judgment such as retry / timeout / give_up and applying status transitions, centrally.

Rationale for the guardrails:
- Why each handler is its own module — even as lifecycle stages grow, "one file = one stage" keeps them isolated and easy to trace.
- Why `status_transitions()` is declarative — the target status per result must be visible in the code so the coordinator can
  apply transitions consistently and leave an audit trail.
- Why responsibility is split — history-based retry/timeout/give_up is not duplicated across handlers; the coordinator handles it centrally.

## Forward direction

- The scheduler will be fully integrated into a reconcile/stages structure (for details, see the manager top-level `AGENTS.md`).
