"""promote a default keypair for users that have none

``a2f6b90c41d7`` carried ``users.main_access_key`` over, which leaves nothing
marked for every user whose value the old ``ON DELETE SET NULL`` foreign key
had already cleared. From this revision on the readers follow the marker, so
those users would keep behaving as if they had no keypair at all.

Promotes their oldest active keypair, the rule ``d3f8c74bf148`` used to
populate ``main_access_key`` in the first place.

Revision ID: f4b1927e0ca8
Revises: a2f6b90c41d7
Create Date: 2026-08-06 17:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4b1927e0ca8"
down_revision = "a2f6b90c41d7"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            UPDATE keypairs
            SET is_default = true
            WHERE keypairs.access_key IN (
                SELECT DISTINCT ON (candidate."user") candidate.access_key
                FROM keypairs AS candidate
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM keypairs AS marked
                    WHERE marked."user" = candidate."user" AND marked.is_default
                )
                ORDER BY candidate."user", candidate.is_active DESC, candidate.created_at ASC
            )
        """)
    )


def downgrade() -> None:
    pass
