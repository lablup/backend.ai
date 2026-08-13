"""rename login_client_types.modified_at to updated_at

``be1ac9308056`` created the column already matching what
``LifecycleTimestampsMixin`` declares -- NOT NULL, ``now()`` server default,
``onupdate`` -- so only the name has to move.

Revision ID: 99365294b8d9
Revises: b9e3a7c14f28
Create Date: 2026-08-13 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "99365294b8d9"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("login_client_types", "modified_at", new_column_name="updated_at")


def downgrade() -> None:
    op.alter_column("login_client_types", "updated_at", new_column_name="modified_at")
