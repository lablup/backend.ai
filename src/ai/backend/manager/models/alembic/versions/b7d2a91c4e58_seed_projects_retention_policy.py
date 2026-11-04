"""seed the projects retention policy

The ``projects`` category was added to ``RetentionCategory`` after the initial seed
migration, so an upgraded database has no policy row for it. Insert one with the
default period and ``enabled = false``; an existing row is left as it stands.

Revision ID: b7d2a91c4e58
Revises: a9c4e2f71b63
Create Date: 2026-11-05 06:35:00.000000

"""

from __future__ import annotations

from datetime import timedelta

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d2a91c4e58"
down_revision = "a9c4e2f71b63"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_INSERT_POLICY = sa.text("""
    INSERT INTO retention_policies (category, retention_period, enabled)
    VALUES (:category, CAST(:period AS interval), false)
    ON CONFLICT (category) DO NOTHING
""")


def upgrade() -> None:
    seed(op.get_bind())


def seed(conn: sa.Connection) -> None:
    """Insert the ``projects`` policy if it is absent. Takes its connection so a test
    can run it against a real database — static analysis does not reach SQL."""
    conn.execute(_INSERT_POLICY, {"category": "projects", "period": timedelta(days=30)})


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM retention_policies WHERE category = 'projects'"))
