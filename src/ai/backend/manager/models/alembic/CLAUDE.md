# Alembic Migrations — Guardrails

> For the full backport procedure and examples, see `README.md` in this directory.

## Rules

- **Backport = fixes only** -- Never backport feature-level schema changes.
- **Idempotent** -- All backport migrations (both `d` and `d'`) must use existence
  checks (`IF NOT EXISTS`, `IF EXISTS`, `inspector`) so they are safe to re-apply.
- **Release version comment** -- Every migration file must have a
  `# Part of: <major>.<minor>.<patch>` comment next to the revision identifiers.
  For backports: `# Part of: 26.2.1 (backport), 26.3.0 (main)`.
- **No revision editing on released migrations** -- Never modify `revision` or
  `down_revision` of a migration that has already been released. Editing
  `down_revision` is allowed only when inserting a backport into the main chain
  before merge.

## Data Migration Verification

Static analysis (lint, mypy) cannot catch SQL-level errors in data migrations.
When a migration does more than DDL — specifically value casting/transformation,
cross-table joins in backfill queries, or conditional backfill logic — you **must**
verify it against the local DB before committing.

### Steps

1. `alembic downgrade` to the parent revision
2. `INSERT` representative test data into the source tables
3. `alembic upgrade` to the target revision
4. `SELECT` from the destination tables and verify converted values
5. Clean up test data or `alembic upgrade head` to continue

### What to cover

- All value formats the application code can produce
  (e.g. BinarySize suffixes like `"32g"`, plain numbers, fractional values like `"0.5"`)
- Null and empty values where the column allows them
- Cross-table references: confirm referenced tables/columns still exist at that
  point in the migration chain
