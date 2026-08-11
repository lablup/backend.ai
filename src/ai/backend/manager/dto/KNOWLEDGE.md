---
name: dto-v1-bucket
type: constraints
description: manager/dto as a de facto REST v1 legacy bucket (new DTOs go to common/dto/manager/v2), the three base classes including the MiddlewareParam context, known layering drift that must not be extended
scope: src/ai/backend/manager/dto
keywords: [BaseRequestModel, BaseResponseModel, MiddlewareParam, REST-v1, legacy]
sources:
  - src/ai/backend/common/api_handlers.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager DTO — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It used to hold the wire types for manager-only API handlers. Today it is
effectively a bucket for the legacy surface — see below.

## The real boundary is API version, not audience

- The nominal boundary is audience scope (manager-only vs shared), but every new feature's DTOs go to `common/dto/manager/v2/` (shared by GraphQL and REST v2).
- This package is therefore effectively the **REST v1 / legacy handler bucket**, and its consumers are almost entirely v1 handlers.
- Add here only when extending a v1 surface that cannot be migrated yet.

## There are three base classes, not one

- Request: `BaseRequestModel` / response: `BaseResponseModel` / middleware-injected context (`RequestCtx`, `UserContext`, ...): `MiddlewareParam` with a `from_request()` constructor.
- All three come from `ai.backend.common.api_handlers`.

## Known drift — do not extend it

- Some of it reaches below its own layer — `request.py` imports ORM rows and repository updaters to provide `to_updater()`, and `context.py` imports enums from models.
- These predate the layering rules — new code does not follow them. Conversion is the adapter's job; keep DTOs pure.
