# Manager DTO — Guardrails

> For API integration patterns that use these DTOs, see the `/api-guide` skill.

## Where to Put a New DTO

| Used by                                          | Location                       |
|--------------------------------------------------|--------------------------------|
| Manager API handlers only                        | `manager/dto/`                 |
| Multiple components (agent, storage, client SDK) | `common/dto/manager/{domain}/` |

When in doubt: if anything outside `manager/` imports it, put it in `common/dto/`.

## DTO Rules

- All DTOs MUST inherit from `BaseRequestModel` (Pydantic v2).
- DTOs handle serialization and validation only — no business logic methods.
- Do NOT import ORM `Row` types from `manager/models/` inside a DTO.
- Do NOT import `data/` domain types into DTOs used by external callers
  (keep the dependency direction: dto → common types only).

## Naming Convention

- Request: `{Operation}{Entity}Req` — e.g., `CreateUserReq`, `SearchSessionsReq`.
- Response: `{Operation}{Entity}Response` — e.g., `CreateUserResponse`.
- Path params: `{Entity}PathParam` — e.g., `ArtifactPathParam`.
