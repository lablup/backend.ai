# Manager sokovan layer: Guardrails

> sokovan is the layer that holds the sokovan coordinator and scheduling, and advances the deployment and route lifecycle in ticks.
> For the operating model and rationale, see `KNOWLEDGE.md` in the same directory (and the `README.md` below it).

## Handler file layout

- **one handler = one file**: every `*Handler` class under `sokovan/**/handlers/` lives in its own module.
- The file name follows the lifecycle stage or sub-step that the handler deals with
  (example: `deploying_provisioning.py`, `deploying_rolling_back.py`, `warming_up.py`, `terminating.py`).
- `base.py` is reserved for the abstract `*Handler` base class. Put shared utilities in a separate module; do not put them in `base.py`.
- Do not put implementations in `__init__.py` (re-exports follow the root global rules).

## Handler vs sokovan coordinator responsibility

- The handler judges and returns only the result of its action (success / failure / skip, etc.). Do not put
  history-based judgment such as retry / timeout / give_up in the handler: the sokovan coordinator handles them centrally.
- Return the failure reason wrapped in `DeploymentExecutionError`.

## Status transitions

- `status_transitions()` must declare the target lifecycle for each result the sokovan coordinator classifies
  (`success`, `need_retry`, `expired`, `give_up`). A result with no target stays in the current status (`coordinator._handle_status_transitions`).
