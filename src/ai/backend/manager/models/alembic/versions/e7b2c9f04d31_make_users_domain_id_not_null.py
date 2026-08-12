"""make users.domain_id NOT NULL

Both creation paths resolve the domain before the insert and fail when it does
not exist, and no update path can write NULL. ``c1a7d3f05e28`` could only fill
the column where ``domain_name`` matched a domain, so the join runs again here.

Revision ID: e7b2c9f04d31
Revises: b9e3a7c14f28
Create Date: 2026-08-12 20:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e7b2c9f04d31"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            UPDATE users u SET domain_id = d.id
            FROM domains d
            WHERE u.domain_id IS NULL AND u.domain_name = d.name
        """)
    )
    op.alter_column("users", "domain_id", existing_type=GUID(), nullable=False)


def downgrade() -> None:
    op.alter_column("users", "domain_id", existing_type=GUID(), nullable=True)
