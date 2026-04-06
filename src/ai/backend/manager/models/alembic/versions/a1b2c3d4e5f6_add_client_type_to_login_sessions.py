"""add client_type to login_sessions

Revision ID: a1b2c3d4e5f6
Revises: d0e1f2a3b4c5
Create Date: 2026-04-06

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "login_sessions",
        sa.Column(
            "client_type",
            sa.String(length=64),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index(
        "ix_login_sessions_user_id_client_type_status",
        "login_sessions",
        ["user_id", "client_type", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_login_sessions_user_id_client_type_status",
        table_name="login_sessions",
    )
    op.drop_column("login_sessions", "client_type")
