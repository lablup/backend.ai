# DTO v2 — Guardrails

## Single Source of Truth

The DTOs in this package are the schema shared by the GraphQL (Strawberry) and REST v2 APIs.
Field names, enum values, and structure must remain stable — both APIs depend on them.
A breaking change here requires a coordinated update of the GQL types and the REST v2 handlers.

## Naming

- Input (request): `Create{Entity}Input`, `Update{Entity}Input`, `Delete{Entity}Input`, `Purge{Entity}Input`
- Node (response): `{Entity}Node`, nested submodels: `{Entity}{Group}Info`
- Payload (mutation result): `Create{Entity}Payload`, `Update{Entity}Payload`, `Delete{Entity}Payload`, `Purge{Entity}Payload`

## File structure

Per domain: `v2/{domain}/types.py`, `request.py`, `response.py`, `__init__.py`

- `types.py` — re-exports domain enums from `common/data/` plus DTO-specific enums (sort fields, direction) and
  nested submodel definitions (e.g., `PermissionSummary`)
- `request.py` — Input models (mapped 1:1 to GQL `@strawberry.input` types)
- `response.py` — Node models (entity representation) and Payload models (mutation results)
- `__init__.py` — avoid re-exports where possible and import modules directly. Use re-exports only when splitting an
  existing single file into a package makes compatibility hard, and afterward avoid re-exports where possible.

## Base classes

- Input models: inherit from `BaseRequestModel` (`ai.backend.common.api_handlers`)
- Node/Payload models: inherit from `BaseResponseModel` (`ai.backend.common.api_handlers`)

## Nesting

- Group semantically related fields into submodels (e.g., `UserBasicInfo`, `UserSecurityInfo`).
- Use a flat structure only when there are fewer than 5 fields and no logical grouping.
- Nested submodels must also inherit from `BaseResponseModel`.
- Avoid nesting deeper than 2 levels to keep serialization predictable.

## Validation

- Use `Field()` constraints: `min_length`, `max_length`, `ge`, `le`, `pattern`.
- Use `field_validator` for cross-field/format validation (e.g., stripping whitespace, verifying non-empty after strip).
- nullable-clearable fields: SENTINEL pattern (sentinel value = "clear this field", None = "no change").
- All optional update fields default to `None` to mean "no change".

## Conversion

- DTOs are pure data structures — no conversion logic inside DTOs.
- Domain Data type → DTO conversion happens in the Adapter layer (`manager/api/adapters/{domain}.py`).
- Do NOT import DB models or domain Data types directly in DTO modules.
