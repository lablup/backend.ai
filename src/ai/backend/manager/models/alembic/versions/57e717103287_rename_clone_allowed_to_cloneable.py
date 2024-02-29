"""rename-clone_allowed-to-cloneable

Revision ID: 57e717103287
Revises: eec98e65902a
Create Date: 2020-10-04 14:14:55.167654

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "57e717103287"
down_revision = "eec98e65902a"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("vfolders", "clone_allowed", new_column_name="cloneable")


def downgrade():
    op.alter_column("vfolders", "cloneable", new_column_name="clone_allowed")
