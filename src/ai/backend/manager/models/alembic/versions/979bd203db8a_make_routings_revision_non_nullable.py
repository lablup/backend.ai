"""make routings.revision non-nullable

Revision ID: 979bd203db8a
Revises: f5338adb2de1, 0a200d0fc480
Create Date: 2026-03-26

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "979bd203db8a"
down_revision = ("f5338adb2de1", "0a200d0fc480")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete orphan routes whose endpoint has no revision
    # (i.e., endpoints with image IS NULL that could not get a revision row).
    op.execute(
        """
        DELETE FROM routings
        WHERE revision IS NULL
        """
    )

    # Make routings.revision NOT NULL now that all routes have a revision.
    op.alter_column("routings", "revision", nullable=False)


def downgrade() -> None:
    op.alter_column("routings", "revision", nullable=True)
