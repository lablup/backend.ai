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
