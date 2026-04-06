"""add client_type to login_sessions

Revision ID: e6036371b6b5
Revises: 04e150fdefa0
Create Date: 2026-04-06

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e6036371b6b5"
down_revision = "04e150fdefa0"
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
