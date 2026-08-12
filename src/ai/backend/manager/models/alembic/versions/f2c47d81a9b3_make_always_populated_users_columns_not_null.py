"""make the always-populated users columns NOT NULL

``totp_activated`` is already NOT NULL in migrated databases; the column is
here for the ones built from the model metadata.

Revision ID: f2c47d81a9b3
Revises: c8d51e7a3b62
Create Date: 2026-08-12 11:20:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "f2c47d81a9b3"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def _backfill(bind: Connection) -> None:
    """The two flags never had a default, so a row that predates one carries NULL."""
    bind.execute(
        sa.text("UPDATE users SET need_password_change = false WHERE need_password_change IS NULL")
    )
    bind.execute(sa.text("UPDATE users SET totp_activated = false WHERE totp_activated IS NULL"))


def upgrade() -> None:
    _backfill(op.get_bind())

    op.alter_column("users", "domain_name", existing_type=sa.String(length=64), nullable=False)
    op.alter_column("users", "role", existing_type=sa.String(length=64), nullable=False)
    op.alter_column(
        "users",
        "need_password_change",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )
    op.alter_column("users", "totp_activated", existing_type=sa.Boolean(), nullable=False)


def downgrade() -> None:
    op.alter_column("users", "domain_name", existing_type=sa.String(length=64), nullable=True)
    op.alter_column("users", "role", existing_type=sa.String(length=64), nullable=True)
    op.alter_column(
        "users",
        "need_password_change",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.alter_column("users", "totp_activated", existing_type=sa.Boolean(), nullable=True)
