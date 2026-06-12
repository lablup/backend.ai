# Alembic migrations — Guardrails

> For the full backport procedure and examples, see `README.md` in this directory.

## Rules

- **Backport = fixes only** — do NOT backport feature-level schema changes.
- **Idempotency** — every backport migration (both `d` and `d'`) must be safe to re-apply by using existence checks
  (`IF NOT EXISTS`, `IF EXISTS`, `inspector`).
- **Release version comment** — every migration file places a
  `# Part of: <major>.<minor>.<patch>` comment next to the revision identifier. For backports: `# Part of: 26.2.1 (backport), 26.3.0 (main)`.
- **Do NOT edit the revision of a released migration** — do not modify the `revision`/`down_revision` of an
  already-released migration. Editing `down_revision` is allowed only when inserting a backport into the main chain before merge.

## Forward direction (under consideration)

- Use `{NEXT_RELEASE_VERSION}` in the version comment so it auto-freezes at release time — do not hardcode the next version
  (the same mechanism as the GQL `added_version`; `scripts/freeze_release_version.py` substitutes across `src/**/*.py`).
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
