# Manager Services layer — Guardrails

> For implementation patterns, see the `/service-guide` skill.

## Directory structure (per domain)

Per domain: `services/{domain}/types.py`, `service.py`, `processors.py`,
and `actions/{base,{operation}}.py` — one file per operation under `actions/`.

`services/ops/` is not a domain: it holds the generic services for the standard six.
An operation whose service method would only forward a repository spec writes no
`service.py` method at all — its action mixes in an `actions/v2/ops/` base and wires
straight to the generic service. Write a domain service method the moment the operation
grows a branch; the generic services take no hook or callback to hide one in.

## Action rules

- Action and ActionResult MUST be `@dataclass(frozen=True)`.
- Exactly one `Action` + `ActionResult` pair per action file.
- Every concrete Action MUST override `entity_id()` and `operation_type()`.
- v2 actions declare `action_name()`, recorded on audit rows: `<verb>_<entity>` in
  lowercase snake_case (plural entity for searches, e.g. `search_resource_slot_types`;
  qualifier prefix where the path differs, e.g. `admin_search_...`). Never derive it
  from the class name — a rename must not split the audit history. The
  `(entity_type, operation_type, action_name)` triple must be unique
  (`tests/unit/manager/actions/test_registry_catalog.py`).

## Service method rules

- Calling multiple repositories from a single service method is discouraged — fix it if the tx is not guaranteed.
  However, when it is entangled with another layer, it is allowed to perform some other action in the service and then call a repository.
- Service methods must NOT create DB sessions/transactions — delegate to the repository.
- Each method takes an Action and returns an ActionResult — no other return type is allowed.

## Processor rules

- Wrap every service method in an `ActionProcessor`. Do NOT expose raw service methods to handlers.
- v2 processors MUST be built through the `ProcessorGroup` factories, passing the action
  class as the first argument — the registry accumulates the wired specs
  (`ProcessorRegistry.wired_specs()`), so no hand-written action list exists.

## What belongs here

- Domain validation and business rules.
- Orchestration across multiple repositories (exceptional, and requires justification).

## What does NOT belong here

- SQL queries or ORM operations.
- HTTP request/response handling.
- Direct DB session creation (`begin_session()` / `begin_readonly_session()`).
