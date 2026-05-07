"""Drop endpoint name unique index

Revision ID: c7d58e2a4f93
Revises: 46e007d9b237
Create Date: 2026-05-07 19:40:00.000000

The partial unique index on (name, domain, project) restricted deployment
name reuse to "active" rows. The list query `my_deployments` is scoped by
`created_user`, so a deployment created by another user in the same project
was invisible to the caller yet still blocked the create — leaving the user
unable to choose the name and unable to locate the conflicting record.

Drop the constraint so deployment names are no longer unique within
(name, domain, project). Routing relies on `route_id`, and the inference
session name template `f"{endpoint.name}-{route_id}"` already disambiguates
on `route_id`, so the index is not load-bearing.

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c7d58e2a4f93"
down_revision = "46e007d9b237"
# Part of: 26.5.0
branch_labels = None
depends_on = None


INDEX_NAME = "ix_endpoints_unique_name_when_active"
PREDICATE = "lifecycle_stage NOT IN ('destroying', 'destroyed')"


def upgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")


def downgrade() -> None:
    op.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} "
        f"ON endpoints (name, domain, project) "
        f"WHERE {PREDICATE}"
    )
