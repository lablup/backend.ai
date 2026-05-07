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

Downgrade caveat: once the upgrade has been applied, users may legitimately
create deployments with duplicate (name, domain, project) tuples. The
downgrade re-creates the partial unique index and therefore fails if such
duplicates exist among active rows. We do not silently mutate user data —
the operator must delete or destroy the duplicate rows before retrying.

"""

from alembic import op
from sqlalchemy.exc import IntegrityError

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
    """Recreate the partial unique index on (name, domain, project).

    If duplicate active deployment names exist (which the dropped index
    previously prevented but which the upgraded schema allows), the
    `CREATE UNIQUE INDEX` raises a unique-violation. Re-raise with a
    guided message instructing the operator to remove the duplicate
    `endpoints` rows before retrying. We do not auto-resolve duplicates
    because endpoint name may carry user-visible meaning and silent
    mutation of user data during a downgrade is unsafe.
    """
    try:
        op.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME} "
            f"ON endpoints (name, domain, project) "
            f"WHERE {PREDICATE}"
        )
    except IntegrityError as exc:
        raise RuntimeError(
            "Cannot recreate the unique index "
            f"`{INDEX_NAME}` on `endpoints (name, domain, project)` "
            "because two or more active deployments share the same name "
            "within the same (domain, project). Delete or destroy the "
            "duplicate `endpoints` rows (or move them to "
            "`lifecycle_stage IN ('destroying', 'destroyed')`) before "
            "retrying this downgrade."
        ) from exc
