# Manager Sokovan layer — Contexts

> For the rules, see `AGENTS.md` in the same directory. For detailed architecture, see `README.md` (and `scheduler/README.md`,
> `deployment/README.md`); for the design, see `proposals/BEP-1030` (status transitions) and `BEP-1033/*`.

## Operating model (tick-based coordinator)

The coordinators (Schedule / Deployment / Route) run one tick periodically, querying entities in the target status and
passing them to the handlers.

- **handler**: judges and returns only the result of its action (success / failure / skip, etc.).
- **coordinator**: takes on history-based judgment such as retry / timeout / give_up and applying status transitions, centrally.

Rationale for the guardrails:
- Why each handler is its own module — even as lifecycle stages grow, "one file = one stage" keeps them isolated and easy to trace.
- Why `status_transitions()` is declarative — the target status per result must be visible in the code so the coordinator can
  apply transitions consistently and leave an audit trail.
- Why responsibility is split — history-based retry/timeout/give_up is not duplicated across handlers; the coordinator handles it centrally.

## Forward direction

- The scheduler will be fully integrated into a reconcile/stages structure (for details, see the manager top-level `AGENTS.md`).
