"""merge the default keypair and service port backfill heads

``a2f6b90c41d7`` and ``55e0c3669e2e`` both branch off ``2dccb3069031`` and were
merged in parallel, leaving two heads. Empty merge so that later migrations
chain onto a single one.

Revision ID: c04f8b1a6e37
Revises: a2f6b90c41d7, 55e0c3669e2e
Create Date: 2026-08-06 17:55:00.000000

"""

# revision identifiers, used by Alembic.
revision = "c04f8b1a6e37"
down_revision = ("a2f6b90c41d7", "55e0c3669e2e")
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
