# Manager component — Guardrails

> For the component overview and architecture, see `src/ai/backend/manager/README.md`.
> For implementation patterns, use the skills referenced by the root `AGENTS.md`.

## Layer order (top → bottom)

```
api/ → services/ → repositories/ → models/
         ↑ data/ and dto/ support all layers
```

## Sub-packages (read the directory's `AGENTS.md` before modifying it)

- `api/` — HTTP/GraphQL handlers
- `services/` — domain validation and business logic
- `repositories/` — DB access
- `models/` — ORM schema
- `data/` — immutable value objects converted to DTOs
- `dto/` — manager-only request/response DTOs
- `views/` — internal-only value objects
- `sokovan/` — coordinator and scheduling

## Cross-layer rules

- Imports follow the layer order — lower layers do NOT import upper layers.
  (`models/` must not import `services/`; `repositories/` must not import `api/`.)
- `data/` types flow upward freely. ORM `Row` types must not cross above `repositories/`.

## Entry points

- `server.py` — HTTP server bootstrap. Changes here affect startup and DI wiring.
- `dependencies/` — dependency assembler. Add new dependencies here, not in `server.py`.
- `event_dispatcher/` — Manager-side event handlers. New event subscriptions go here.

## Errors

- Both `manager/exceptions.py` and `manager/errors/` exist, but `errors/` is the current standard.
- Put new domain exceptions in `manager/errors/{domain}.py` — not in `manager/exceptions.py`.

## Scheduler

- Place scheduling logic in `manager/sokovan/scheduler/` — do NOT make scheduling decisions inside
  API handlers or service methods.
- **Forward direction:** the scheduler will be fully integrated into sokovan's reconcile/stages structure.
