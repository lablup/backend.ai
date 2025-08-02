"""migrate vfolder data to rbac table

Revision ID: 4a60160ba8e0
Revises: 643deb439458
Create Date: 2025-07-30 14:44:14.346887

"""

from alembic import op

from ai.backend.manager.models.rbac_models.migrate.vfolder import migrate_vfolder_data

# revision identifiers, used by Alembic.
revision = "4a60160ba8e0"
down_revision = "643deb439458"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    migrate_vfolder_data(conn)


def downgrade() -> None:
    pass
