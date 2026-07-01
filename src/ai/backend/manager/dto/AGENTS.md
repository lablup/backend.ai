# Manager DTO — Guardrails

> For the API integration patterns that use these DTOs, see the `/api-guide` skill.

## Where to put a new DTO

| Used by | Location |
|-----------|------|
| Manager API handlers only | `manager/dto/` |
| Multiple components (agent, storage, client SDK) | `common/dto/manager/{domain}/` |

When unsure: if it is imported from outside `manager/`, put it in `common/dto/`.

## DTO rules

- Every DTO must inherit `BaseRequestModel` (Pydantic v2).
- DTOs are for serialization/validation only — no business-logic methods.
- Do NOT import ORM `Row` types from `manager/models/` inside a DTO.
- Do NOT import `data/` domain types into a DTO used by external callers (preserve the dependency direction: dto → common types only).

## Naming convention

- Request: `{Operation}{Entity}Req` — e.g. `CreateUserReq`, `SearchSessionsReq`.
- Response: `{Operation}{Entity}Response` — e.g. `CreateUserResponse`.
- Path parameter: `{Entity}PathParam` — e.g. `ArtifactPathParam`.
