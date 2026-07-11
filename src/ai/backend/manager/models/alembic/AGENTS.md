# Alembic migrations — Guardrails

> For the full backport procedure and examples, see `README.md` in this directory.

## Rules

- **Backport = fixes only** — do NOT backport feature-level schema changes.
- **Idempotency** — every backport migration (both `d` and `d'`) must be safe to re-apply by using existence checks
  (`IF NOT EXISTS`, `IF EXISTS`, `inspector`).
- **Release version comment** — every migration file places a `# Part of: NEXT_RELEASE_VERSION` comment next to the
  revision identifier. Do NOT hardcode a version; the `NEXT_RELEASE_VERSION` placeholder is frozen to the actual version. For backports the placeholder freezes per branch, so both `d` and `d'` keep the same placeholder.
- **Do NOT edit the revision of a released migration** — do not modify the `revision`/`down_revision` of an
  already-released migration. Editing `down_revision` is allowed only when inserting a backport into the main chain before merge.

## Forward direction (under consideration)

- Avoid adding alembic migrations in a backport where possible. If you must, place the corresponding version on the backport
  branch, and afterwards reconcile so that main also includes that downgrade.

## Data migration verification

Static analysis (lint, mypy) cannot catch SQL-level errors in data migrations. When a migration goes beyond DDL to perform
value casting/conversion, cross-table joins in backfill queries, or conditional backfill logic, you **must** verify it
against a local DB before committing.

### Steps

1. `alembic downgrade` to the parent revision
2. `INSERT` representative test data into the source table
3. `alembic upgrade` to the target revision
4. `SELECT` the target table to verify the converted values
5. Clean up the test data, or continue with `alembic upgrade head`

### What to cover

- Every value format the application code can produce (e.g. BinarySize suffix `"32g"`, plain numbers, fractions `"0.5"`)
- The null/empty values the column allows
- Cross-table references: confirm that the referenced table/column still exists at that point in the migration chain
