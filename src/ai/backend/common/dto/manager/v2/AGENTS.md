# DTO v2 Rules

## Single Source of Truth

DTOs in this package are the shared schema for both GraphQL (Strawberry) and REST v2 APIs.
Field names, enum values, and structure must remain stable — both APIs depend on them.
Any breaking change here requires coordinated updates in GQL types and REST v2 handlers.

## Naming

- Input (request): `Create{Entity}Input`, `Update{Entity}Input`, `Delete{Entity}Input`, `Purge{Entity}Input`
- Node (response): `{Entity}Node`, nested sub-models: `{Entity}{Group}Info`
- Payload (mutation result): `Create{Entity}Payload`, `Update{Entity}Payload`, `Delete{Entity}Payload`, `Purge{Entity}Payload`

## File Structure

Per domain: `v2/{domain}/types.py`, `request.py`, `response.py`, `__init__.py`

- `types.py` — re-export domain enums from `common/data/` plus define DTO-specific enums (order fields, directions) and nested sub-models (e.g., `PermissionSummary`)
- `request.py` — Input models (map 1:1 with GQL `@strawberry.input` types)
- `response.py` — Node models (entity representation) and Payload models (mutation results)
- `__init__.py` — re-export all public names from all three modules

## Base Classes

- Input models: inherit from `BaseRequestModel` (from `ai.backend.common.api_handlers`)
- Node/Payload models: inherit from `BaseResponseModel` (from `ai.backend.common.api_handlers`)

## Nesting

- Group semantically related fields into sub-models (e.g., `UserBasicInfo`, `UserSecurityInfo`)
- Use flat structure only when fields < 5 and no logical grouping exists
- Nested sub-models must also inherit from `BaseResponseModel`
- Avoid deeply nested structures (> 2 levels) to keep serialization predictable

## Validation

- Use `Field()` constraints: `min_length`, `max_length`, `ge`, `le`, `pattern`
- Use `field_validator` for cross-field or format validation (e.g., strip whitespace, validate non-empty after strip)
- Nullable-clearable fields: use SENTINEL pattern (sentinel value signals "clear this field" vs. None meaning "no change")
- All optional update fields default to `None` to represent "no change"

## Conversion

- DTO is a pure data structure — no conversion logic inside DTOs
- Conversion from domain Data types to DTOs is performed in the Adapter layer (`manager/api/adapters/{domain}.py`)
- No direct DB model or domain Data type imports in DTO modules
