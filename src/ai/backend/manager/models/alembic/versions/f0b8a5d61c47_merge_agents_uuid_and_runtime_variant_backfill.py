"""merge agents uuid and runtime variant backfill heads

``13f4b8bc37f2`` and ``d366a4c96f75`` were merged independently and left two
heads. Empty merge so that later migrations chain onto a single one.

Revision ID: f0b8a5d61c47
Revises: 13f4b8bc37f2, d366a4c96f75
Create Date: 2026-08-06 11:40:00.000000

"""

# revision identifiers, used by Alembic.
revision = "f0b8a5d61c47"
down_revision = ("13f4b8bc37f2", "d366a4c96f75")
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
