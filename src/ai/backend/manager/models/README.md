# DB ORM Model Design Guidelines

This document holds guidelines for designing SQLAlchemy ORM models in the Backend.AI manager.

## Core Principles

### Responsibility Scope

- **models**: Table schema definition, column types, relationships, indexes, and `to_data()` conversion methods
- **repositories**: All query logic (create, get, update, delete, retrieval, aggregation, and the like)

Query methods such as `get_by_id` and `list_by_condition` belong in repositories, not models.

### Model Definition

- Define ORM Row classes by inheriting from `Base`.
- Set the table name with the `__tablename__` attribute (plural snake_case: `sessions`, `kernels`).

## Column Types

### Primary Key

- Prefer `IDColumn()`.
- Domain-specific ID types ensure type safety: `SessionIDColumn()`, `KernelIDColumn()`, `EndpointIDColumn()`.

### Reference Columns

- Use ID (UUID) columns without a DB-level foreign key constraint.
- Repositories fetch related rows in queries, not through `relationship()`.

### Enum

- Use `StrEnumType` to store the value as a string.
- This helps debugging and migration.

### JSONB

- The value is stored as unstructured data in the DB. Define its structure with Pydantic models on the server side for type safety.
- `StructuredJSONObjectColumn` and `StructuredJSONObjectListColumn` integrate with Pydantic models automatically.
- SQL aggregation cannot access fields inside JSONB, so process them in Python.

### Date/Time

- Always use `sa.DateTime(timezone=True)`, stored in UTC.
- Create a `created_at` column (it supports cursor pagination).
- Record timestamps such as `created_at` and `updated_at` from DB time automatically, not by hand.
  - On creation: `server_default=sa.func.now()`
  - On update: `onupdate=sa.func.now()` or `server_onupdate=sa.func.now()`

## Default Value Settings

Use only one of `server_default` and `default`. Choose by use case.

### server_default

Sets the default at the DB level. It applies even when SQL runs directly.

- Timestamps: `created_at`, `updated_at`
- UUID auto-generation
- Initial status values
- Boolean defaults

### default

Sets the default at the Python level. It applies only when a row is created through the ORM.

- Mutable objects such as an empty dict or list: `environ`, `tags`
- Python constant references: `priority` (`SESSION_PRIORITY_DEFAULT` and the like)
- An Enum default given as a Python object: `status`
- A value that needs dynamic generation through a callable

### When Not to Use Default Values

- Required input fields: columns that must be set explicitly on creation (`name`, `user_uuid`, and the like)
- Reference columns: the reference target must be set explicitly
- A column with `nullable=True` where NULL is a meaningful default state: `terminated_at`, `deleted_at`

### Usage with nullable

- `nullable=False` and `server_default`: the default value applies to existing rows during migration.
- `nullable=True` and `default=sa.null()`: allow NULL explicitly.

## Relationship Definition

- Define no new `relationship()` attributes on Row classes. Fetch related rows with repository queries.
- Existing relationships are being removed. When the last reference to one disappears, delete it together with its `back_populates` pair on the other side.
- Association table naming: `association_{tableA}_{tableB}`

## Index Design

Consider indexes for these columns:

- **WHERE clause**: columns that are filtered often, such as `status`, `domain_name`, `scaling_group_name`
- **ORDER BY clause**: columns used for sorting, such as `created_at`, `priority`
- **Reference columns**: these improve lookup performance for queries on referenced rows
- **Compound conditions**: column combinations used together often

Index types:
- Single column: `index=True`
- Compound/GIN/conditional: use `sa.Index()` in `__table_args__`

## Data Conversion

### to_data() Method

Implement `to_data()` to convert an ORM Row to a dataclass.

- Convert Enum values to the appropriate types.
- Convert JSONB data to structured models with Pydantic `model_validate()`.

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

- [ ] Inherit `Base` and define `__tablename__`.
- [ ] Primary key: `IDColumn()` or a domain-specific ID
- [ ] Reference columns: ID (UUID) based, with no DB-level foreign key constraint
- [ ] Set `nullable` explicitly
- [ ] Set `server_default` or `default`, one only
- [ ] Include a `created_at` column (cursor pagination)
- [ ] Add the necessary indexes (consider WHERE and ORDER BY)
- [ ] No `relationship()` attributes: related rows come from repository queries
- [ ] Implement the `to_data()` conversion method
- [ ] Generate an Alembic migration
