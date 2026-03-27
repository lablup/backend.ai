# Manager Services Layer — Guardrails

> For full implementation patterns, see the `/service-guide` skill.

## Directory Structure (per domain)

Each domain follows: `services/{domain}/types.py`, `service.py`, `processors.py`,
and `actions/{base,{operation}}.py` — one file per operation under `actions/`.

## Action Rules

- Actions and ActionResults MUST be `@dataclass(frozen=True)`.
- Every action file contains exactly ONE `Action` + ONE `ActionResult` pair.
- `entity_id()` and `operation_type()` must be overridden in every concrete Action.

## Service Method Rules

- One service method = one repository call (preferred). If multiple repository calls are
  required, add a comment explaining why.
- Service methods MUST NOT create DB sessions or transactions — delegate to the Repository.
- Each method accepts an Action and returns an ActionResult — no other return types.

## Processor Rules

- Wrap every service method in an `ActionProcessor`; never expose raw service methods to handlers.
- `AbstractProcessorPackage` must be subclassed; `supported_actions()` must be overridden.

## What Belongs Here

- Domain validation and business rules.
- Orchestration across multiple repositories (exceptional, must be justified).

## What Does NOT Belong Here

- SQL queries or ORM operations.
- HTTP request/response handling.
- Direct DB session creation (`begin_session()` / `begin_readonly_session()`).
