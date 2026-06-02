# Manager Sokovan Layer — Guardrails

> Sokovan is the coordinator layer that advances deployment / route
> lifecycles tick by tick.

## Handler File Layout

- **One handler = one file**: every `*Handler` class under
  `sokovan/**/handlers/` lives in its own module.
- Name the file after the lifecycle stage or sub-step it handles
  (e.g., `deploying_provisioning.py`, `deploying_rolling_back.py`,
  `warming_up.py`, `terminating.py`).
- `base.py` is reserved for the abstract `*Handler` base class. Put
  shared utilities in their own module — never in `base.py`.
- `__init__.py` only re-exports handler classes; it must not contain
  implementation.

## Status Transitions

- `status_transitions()` must declare the target lifecycle for each
  outcome (`success`, `need_retry`, `expired`, `give_up`). Outcomes
  with no target stay in the current state
  (see `coordinator._handle_status_transitions`).
- The coordinator classifies failures from history; handlers only
  return the failure reason in `DeploymentExecutionError`.
