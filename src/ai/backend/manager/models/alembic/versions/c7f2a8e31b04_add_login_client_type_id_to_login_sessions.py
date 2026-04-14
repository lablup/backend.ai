"""add login_client_type_id to login_sessions

Revision ID: c7f2a8e31b04
Revises: b4e7f1a2c3d5
Create Date: 2026-04-14

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c7f2a8e31b04"
down_revision = "b4e7f1a2c3d5"
# Part of: 26.3.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "login_sessions",
        sa.Column(
            "login_client_type_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_login_sessions_login_client_type_id",
        "login_sessions",
        "login_client_types",
        ["login_client_type_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_login_sessions_login_client_type_id",
        "login_sessions",
        ["login_client_type_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_login_sessions_login_client_type_id", table_name="login_sessions")
    op.drop_constraint(
        "fk_login_sessions_login_client_type_id", "login_sessions", type_="foreignkey"
    )
    op.drop_column("login_sessions", "login_client_type_id")
