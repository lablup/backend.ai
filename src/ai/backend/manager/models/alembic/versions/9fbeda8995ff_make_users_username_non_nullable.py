"""Make users.username non-nullable

Rows without a username are backfilled with their email, mirroring the
signup-service default.

Create Date: 2026-08-03

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9fbeda8995ff"
down_revision = "857c4d02c4b9"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET username = email WHERE username IS NULL")
    op.alter_column("users", "username", nullable=False)


def downgrade() -> None:
    op.alter_column("users", "username", nullable=True)
