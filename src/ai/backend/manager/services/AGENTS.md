# Manager Services layer — Guardrails

> For implementation patterns, see the `/service-guide` skill.

## Directory structure (per domain)

Per domain: `services/{domain}/types.py`, `service.py`, `processors.py`,
and `actions/{base,{operation}}.py` — one file per operation under `actions/`.

## Action rules

- Action and ActionResult MUST be `@dataclass(frozen=True)`.
- Exactly one `Action` + `ActionResult` pair per action file.
- Every concrete Action MUST override `entity_id()` and `operation_type()`.

## Service method rules

- Calling multiple repositories from a single service method is discouraged — fix it if the tx is not guaranteed.
  However, when it is entangled with another layer, it is allowed to perform some other action in the service and then call a repository.
- Service methods must NOT create DB sessions/transactions — delegate to the repository.
- Each method takes an Action and returns an ActionResult — no other return type is allowed.

## Processor rules

- Wrap every service method in an `ActionProcessor`. Do NOT expose raw service methods to handlers.
- It MUST inherit from `AbstractProcessorPackage` and override `supported_actions()`.

## What belongs here

- Domain validation and business rules.
- Orchestration across multiple repositories (exceptional, and requires justification).

## What does NOT belong here

- SQL queries or ORM operations.
- HTTP request/response handling.
- Direct DB session creation (`begin_session()` / `begin_readonly_session()`).
