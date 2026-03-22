# Manager Component — Guardrails

> For component overview and architecture, see `src/ai/backend/manager/README.md`.
> For implementation patterns, use the skills referenced in the root `CLAUDE.md`.

## Layer Order (top → bottom)

```
api/ → services/ → repositories/ → models/
         ↑ data/ and dto/ serve all layers
```

Each layer has its own `CLAUDE.md`. Read it before modifying code in that directory.

## Cross-Layer Rules

- Imports MUST follow the layer order — lower layers must never import from upper layers.
  (`models/` must not import from `services/`; `repositories/` must not import from `api/`.)
- `data/` types flow upward freely; ORM `Row` types must not cross above `repositories/`.

## Entry Points

- `server.py` — HTTP server bootstrap. Changes here affect startup and DI wiring.
- `dependencies/` — Dependency composer. Add new dependencies here, not in `server.py`.
- `event_dispatcher/` — Manager-side event handlers. New event subscriptions go here.

## Errors

- `manager/exceptions.py` and `manager/errors/` both exist; `errors/` is the current standard.
- New domain exceptions go in `manager/errors/{domain}.py` — not in `manager/exceptions.py`.

## Scheduler

- Scheduling logic belongs in `manager/scheduler/` — do not add scheduling decisions inside
  API handlers or service methods.
