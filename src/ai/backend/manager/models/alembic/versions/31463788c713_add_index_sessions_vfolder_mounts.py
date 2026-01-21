"""add_index_sessions_vfolder_mounts

Revision ID: 31463788c713
Revises: dddf9be580f5
Create Date: 2024-04-19 18:53:29.903113

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "31463788c713"
down_revision = "dddf9be580f5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_sessions_vfolder_mounts",
        "sessions",
        ["vfolder_mounts"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index("ix_sessions_vfolder_mounts", table_name="sessions", postgresql_using="gin")
