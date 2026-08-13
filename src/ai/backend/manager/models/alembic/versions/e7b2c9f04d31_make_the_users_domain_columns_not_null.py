"""make the users domain columns NOT NULL

Both creation paths resolve the domain before the insert and fail when it does
not exist, and no update path can write NULL. A row that predates that takes
the half it is missing from the other, and one missing both joins the domain
``b9e3a7c14f28`` marks as the default.

Revision ID: e7b2c9f04d31
Revises: b9e3a7c14f28
Create Date: 2026-08-12 20:40:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e7b2c9f04d31"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def _backfill(bind: Connection) -> None:
    bind.execute(
        sa.text("""
            UPDATE users u SET domain_id = d.id
            FROM domains d
            WHERE u.domain_id IS NULL AND u.domain_name = d.name
        """)
    )
    bind.execute(
        sa.text("""
            UPDATE users u SET domain_name = d.name
            FROM domains d
            WHERE u.domain_name IS NULL AND u.domain_id = d.id
        """)
    )
    bind.execute(
        sa.text("""
            UPDATE users u SET domain_name = d.name, domain_id = d.id
            FROM domains d
            WHERE (u.domain_name IS NULL OR u.domain_id IS NULL) AND d.is_default
        """)
    )


def upgrade() -> None:
    _backfill(op.get_bind())
    op.alter_column("users", "domain_name", existing_type=sa.String(length=64), nullable=False)
    op.alter_column("users", "domain_id", existing_type=GUID(), nullable=False)


def downgrade() -> None:
    op.alter_column("users", "domain_id", existing_type=GUID(), nullable=True)
    op.alter_column("users", "domain_name", existing_type=sa.String(length=64), nullable=True)
