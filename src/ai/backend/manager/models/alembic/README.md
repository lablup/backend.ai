# Alembic Migrations

Generic single-database configuration.

## Migration Backport Strategy

This section describes how to safely backport Alembic migrations to release branches
while keeping the main branch consistent.

The same strategy applies to all components:

| Component | Alembic directory |
|---|---|
| Manager | `src/ai/backend/manager/models/alembic/` |
| Account Manager | `src/ai/backend/account_manager/models/alembic/` |
| App Proxy Coordinator | `src/ai/backend/appproxy/coordinator/models/alembic/` |

### Principles

1. **Fixes only** -- Backport migrations must contain schema fixes only (e.g., missing
   columns, incorrect types, enum coexistence issues). Feature-level schema changes are
   never backported.
2. **Idempotent** -- Both the backport migration and its duplicate on main must be
   idempotent so they are safe to re-apply on databases that may already have the change.
3. **No manual revision editing** -- Never modify the `revision` or `down_revision` of
   an existing migration that has already been released. Editing `down_revision` is
   allowed only when inserting a backport migration into the main branch chain before
   the change is merged (see Step 2 below).
4. **Linear chain** -- The migration chain must always remain linear (single head).
   Never create merge migrations. If multiple heads appear after inserting a backport,
   fix the `down_revision` pointers instead.

### Backport Procedure

Given the following migration chain on **main**:

```
a  -->  b  -->  c        (a = backport target head, c = main head)
```

#### Step 1: Create migration `d` on the release branch

On the release branch, create a new migration whose `down_revision` is `a` (the
release branch head at the point you are targeting):

```
a  -->  d                 (release branch result)
```

#### Step 2: Insert `d` into main and add duplicate `d'`

On **main**, the same migration `d` is inserted between `a` and `b`, and a duplicate
`d'` is appended on top of the current main head `c`:

```
a  -->  d  -->  b  -->  c  -->  d'
```

- `d` — Set `down_revision = a` and `revision` to the same value used on the release
  branch. Update `b`'s `down_revision` to point to `d`.
- `d'` — A new migration file with a fresh revision ID, `down_revision = c`, that
  performs the **same schema change** as `d` but written idempotently so it is a no-op
  on databases that already applied `d`.

### Release Version Comment

Every migration file must include a comment indicating which release version
(including the minor version, e.g., `26.3.0`) it belongs to. Place the comment
next to the revision identifiers:

```python
# revision identifiers, used by Alembic.
revision = "1cc9b47e0a8e"
down_revision = "ffcf0ed13a26"
# Part of: 26.3.0
branch_labels = None
depends_on = None
```

For backport migrations, note both the target release branch and the main branch:

```python
# Part of: 26.2.1 (backport), 26.3.0 (main)
```

### Idempotent Writing Rules

Every backport migration (both `d` and `d'`) **must** be idempotent. Use the following
patterns:

#### DDL guards

```python
# Creating a table
conn = op.get_bind()
inspector = sa.inspect(conn)
if "my_table" not in inspector.get_table_names():
    op.create_table("my_table", ...)

# Adding a column
columns = [c["name"] for c in inspector.get_columns("my_table")]
if "new_col" not in columns:
    op.add_column("my_table", sa.Column("new_col", sa.String))

# Creating an index
indexes = [idx["name"] for idx in inspector.get_indexes("my_table")]
if "ix_my_table_col" not in indexes:
    op.create_index("ix_my_table_col", "my_table", ["col"])
```

#### Enum type guards

```python
conn = op.get_bind()
result = conn.exec_driver_sql(
    "SELECT 1 FROM pg_type WHERE typname = 'myenum'"
)
if result.fetchone() is None:
    # Create the enum type
    my_enum = sa.Enum("A", "B", name="myenum")
    my_enum.create(conn)
```

#### Raw SQL guards

```sql
-- Column
ALTER TABLE my_table ADD COLUMN IF NOT EXISTS new_col TEXT;

-- Index
CREATE INDEX IF NOT EXISTS ix_my_table_col ON my_table (col);

-- Dropping
DROP INDEX IF EXISTS ix_my_table_col;
ALTER TABLE my_table DROP COLUMN IF EXISTS old_col;
```

#### Downgrade

Downgrade functions follow the same idempotent rules. If the downgrade is handled by
another migration in the chain, use `pass`:

```python
def downgrade() -> None:
    pass
```

### Real-World Examples

See the following migrations in the codebase for reference:

- `src/ai/backend/manager/models/alembic/versions/1cc9b47e0a8e_fix_sessionresult_enum_type_coexistence_backport.py`
  -- Checks multiple possible enum states and fixes whichever scenario it finds.
- `src/ai/backend/manager/models/alembic/versions/c4ea15b77136_ensure_auditlogs_table_exist.py`
  -- Uses `inspector.get_table_names()` to skip table creation when it already exists.
