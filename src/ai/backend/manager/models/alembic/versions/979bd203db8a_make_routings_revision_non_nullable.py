"""make routings.revision non-nullable

Revision ID: 979bd203db8a
Revises: 930e9f2dd502
Create Date: 2026-03-26

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "979bd203db8a"
down_revision = "930e9f2dd502"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete all routes with NULL revision.
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
