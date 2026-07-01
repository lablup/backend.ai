"""Narrow endpoint name unique index to active states

Revision ID: 2a531e0c528e
Revises: b4e7f1a2c3d5
Create Date: 2026-04-14 11:00:00.000000

The previous predicate `lifecycle_stage != 'destroyed'` left DESTROYING rows in
the partial unique index. Updating `lifecycle_stage` (a predicate column) caused
Postgres to re-insert the index entry for the new tuple, which conflicted with
any sibling row that also still satisfied the old predicate. Restricting the
predicate to active states removes both DESTROYING and DESTROYED rows from the
index so that `update_endpoint_lifecycle(..., DESTROYING)` no longer races
against the index.

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a531e0c528e"
down_revision = "b4e7f1a2c3d5"
# Part of: 26.4.2
branch_labels = None
depends_on = None


OLD_INDEX_NAME = "ix_endpoints_unique_name_when_not_destroyed"
NEW_INDEX_NAME = "ix_endpoints_unique_name_when_active"
OLD_PREDICATE = "lifecycle_stage != 'destroyed'"
NEW_PREDICATE = "lifecycle_stage NOT IN ('destroying', 'destroyed')"


def upgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {OLD_INDEX_NAME}")
    op.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {NEW_INDEX_NAME} "
        f"ON endpoints (name, domain, project) "
        f"WHERE {NEW_PREDICATE}"
    )


def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {NEW_INDEX_NAME}")
    op.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {OLD_INDEX_NAME} "
        f"ON endpoints (name, domain, project) "
        f"WHERE {OLD_PREDICATE}"
    )
