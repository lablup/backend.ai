# DB ORM Model Design Guidelines

This document provides guidelines for designing SQLAlchemy ORM models in Backend.AI Manager.

## Core Principles

### Responsibility Scope

- **models**: Table schema definition, column types, relationships, indexes, `to_data()` conversion methods
- **repositories**: All query logic (CRUD, retrieval, aggregation, etc.)

Query-related methods (`get_by_id`, `list_by_condition`, etc.) should be implemented in repositories, not models.

### Model Definition

- Define ORM Row classes by inheriting from `Base`
- Specify table name using `__tablename__` attribute (plural snake_case: `sessions`, `kernels`)

## Column Types

### Primary Key

- Use `IDColumn()` recommended
- Domain-specific ID types ensure type safety: `SessionIDColumn()`, `KernelIDColumn()`, `EndpointIDColumn()`

### Reference Columns

- Use ID(UUID) columns without DB-level Foreign Key constraints
- Relationships are defined via SQLAlchemy `relationship()` with `primaryjoin`

### Enum

- Use `StrEnumType` to store as string
- Beneficial for debugging and migration

### JSONB

- Stored as unstructured data in DB, but define structure with Pydantic models on server side for type safety
- `StructuredJSONObjectColumn`, `StructuredJSONObjectListColumn` automatically integrate with Pydantic models
- JSONB internal fields cannot use SQL aggregation → process in Python

### Date/Time

- Always use `sa.DateTime(timezone=True)` (stored in UTC)
- Recommend creating `created_at` column (supports cursor pagination)
- Timestamps like `created_at`, `updated_at` should be automatically recorded based on DB time, not manually set
  - On creation: `server_default=sa.func.now()`
  - On update: `onupdate=sa.func.now()` or `server_onupdate=sa.func.now()`

## Default Value Settings

Use only one of `server_default` or `default`. Choose appropriately based on use case.

### server_default

Sets default at DB level. Applied even when executing SQL directly.

- Timestamps: `created_at`, `updated_at`
- UUID auto-generation
- Initial status values
- Boolean defaults

### default

Sets default at Python level. Applied only when creating via ORM.

- Mutable objects like empty dict/list: `environ`, `tags`
- Python constant references: `priority` (SESSION_PRIORITY_DEFAULT, etc.)
- When specifying Enum default as Python object: `status`
- When dynamic generation via callable is needed

### When Not to Use Default Values

- Required input fields: Columns that must be explicitly specified on creation (`name`, `user_uuid`, etc.)
- Reference columns: Reference target must be explicitly specified
- When `nullable=True` and NULL itself is a meaningful default state: `terminated_at`, `deleted_at`

### Usage with nullable

- `nullable=False` + `server_default`: Default value applied to existing rows during migration
- `nullable=True` + `default=sa.null()`: Explicitly allow NULL

## Relationship Definition

- `back_populates` is required for bidirectional relationships
- Specify `primaryjoin`, `foreign_keys` for complex join conditions
- Association table naming: `association_{tableA}_{tableB}`

## Index Design

Consider indexes for the following columns:

- **WHERE clause**: Frequently filtered columns like `status`, `domain_name`, `scaling_group_name`
- **ORDER BY clause**: Columns used for sorting like `created_at`, `priority`
- **Reference columns**: Improves relationship query performance
- **Compound conditions**: Column combinations frequently used together

Index types:
- Single column: `index=True`
- Compound/GIN/Conditional: Use `sa.Index()` in `__table_args__`

## Data Conversion

### to_data() Method

Implement `to_data()` method to convert ORM Row to dataclass.

- Convert Enum values to appropriate types
- Convert JSONB data to structured models using Pydantic `model_validate()`
- Extract only necessary fields from relationship data

## Naming Conventions

| Target | Rule | Example |
|--------|------|---------|
| Table name | Plural snake_case | `sessions`, `scaling_groups` |
| Column name | snake_case | `created_at`, `user_uuid` |
| Boolean column | Adjective or past participle | `schedulable`, `deleted`, `enabled` |
| Reference column | `{referenced_table}_id` | `group_id`, `user_uuid` |
| Index | `ix_{table}_{columns}` | `ix_sessions_status_priority` |
| Unique constraint | `uq_{table}_{columns}` | `uq_sessions_name_domain` |
| Row class | `{Entity}Row` | `SessionRow`, `KernelRow` |

## Checklist

When adding a new model:

- [ ] Inherit `Base`, define `__tablename__`
- [ ] Primary Key: `IDColumn()` or domain-specific ID
- [ ] Reference columns: ID(UUID) based, no DB-level FK constraints
- [ ] Explicitly specify `nullable`
- [ ] Set `server_default` or `default` (only one)
- [ ] Include `created_at` column (cursor pagination)
- [ ] Add necessary indexes (consider WHERE, ORDER BY)
- [ ] Set `back_populates` for bidirectional relationships
- [ ] Implement `to_data()` conversion method
- [ ] Generate Alembic migration
