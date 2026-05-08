"""Drop endpoint name unique index

Revision ID: c7d58e2a4f93
Revises: 3632aad9d5d9
Create Date: 2026-05-07 19:40:00.000000

Drop the partial unique index on (name, domain, project). The previous
scope did not match `my_deployments` (which is scoped by `created_user`),
so a deployment by another user in the same project blocked creates while
staying invisible to the caller.

Downgrade fails if active rows now hold duplicate (name, domain, project);
operator must dedupe first.

"""

from alembic import op
from sqlalchemy.exc import IntegrityError

# revision identifiers, used by Alembic.
revision = "c7d58e2a4f93"
down_revision = "3632aad9d5d9"
# Part of: 26.5.0
branch_labels = None
depends_on = None


INDEX_NAME = "ix_endpoints_unique_name_when_active"
PREDICATE = "lifecycle_stage NOT IN ('destroying', 'destroyed')"


def upgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")


def downgrade() -> None:
    try:
        op.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} "
            f"ON endpoints (name, domain, project) "
            f"WHERE {PREDICATE}"
        )
    except IntegrityError as exc:
        raise RuntimeError(
            f"Duplicate (name, domain, project) among active `endpoints` rows; "
            f"delete duplicates before retrying downgrade to recreate `{INDEX_NAME}`."
        ) from exc
