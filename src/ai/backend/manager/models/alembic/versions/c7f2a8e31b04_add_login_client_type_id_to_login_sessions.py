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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("login_sessions")]
    if "login_client_type_id" not in columns:
        op.add_column(
            "login_sessions",
            sa.Column(
                "login_client_type_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )

    fk_columns = [fk["constrained_columns"] for fk in inspector.get_foreign_keys("login_sessions")]
    if ["login_client_type_id"] not in fk_columns:
        op.create_foreign_key(
            "fk_login_sessions_login_client_type_id",
            "login_sessions",
            "login_client_types",
            ["login_client_type_id"],
            ["id"],
            ondelete="SET NULL",
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("login_sessions")]
    if "ix_login_sessions_login_client_type_id" not in indexes:
        op.create_index(
            "ix_login_sessions_login_client_type_id",
            "login_sessions",
            ["login_client_type_id"],
        )


def downgrade() -> None:
    op.drop_index("ix_login_sessions_login_client_type_id", table_name="login_sessions")
    op.drop_column("login_sessions", "login_client_type_id")
