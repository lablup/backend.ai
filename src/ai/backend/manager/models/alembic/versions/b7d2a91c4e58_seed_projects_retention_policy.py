"""seed the projects retention policy

The ``projects`` category was added to ``RetentionCategory`` after the initial seed
migration, so an upgraded database has no policy row for it. Insert one with the
default period and ``enabled = false``; an existing row is left as it stands. The id
is the one in ``seeds/manager/retention_policy/defaults.yaml``, so applying the seed
files to this database updates that row instead of adding a second one.

Revision ID: b7d2a91c4e58
Revises: a9c4e2f71b63
Create Date: 2026-11-05 06:35:00.000000

"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d2a91c4e58"
down_revision = "a9c4e2f71b63"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_PROJECTS_POLICY_ID = UUID("b1e5f4a0-0009-4c10-8a01-000000000009")

_INSERT_POLICY = sa.text("""
    INSERT INTO retention_policies (id, category, retention_period, enabled)
    VALUES (:id, :category, CAST(:period AS interval), false)
    ON CONFLICT (category) DO NOTHING
""")


def upgrade() -> None:
    seed(op.get_bind())


def seed(conn: sa.Connection) -> None:
    """Insert the ``projects`` policy if it is absent. Takes its connection so a test
    can run it against a real database — static analysis does not reach SQL."""
    conn.execute(
        _INSERT_POLICY,
        {"id": _PROJECTS_POLICY_ID, "category": "projects", "period": timedelta(days=30)},
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM retention_policies WHERE category = 'projects'"))
