# DTO v2 Rules

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

- Node models MUST have `from_data(cls, data: {Entity}Data) -> Self` classmethod
- For detailed data: `from_detail_data(cls, data: {Entity}DetailData) -> Self` classmethod
- No direct DB model imports — only domain data types from `common/data/` or `manager/data/`
- Conversion classmethods must be type-safe (no `type: ignore`)
