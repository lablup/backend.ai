"""add is_default to keypairs

Which keypair is a user's main one is recorded on ``users.main_access_key``,
whose foreign key is ``ON DELETE SET NULL`` — deleting any keypair silently
clears it. The fact describes a keypair, so it moves onto ``keypairs``, where
deleting the row takes the fact with it.

Backfills only keypairs that their own user points at; a ``main_access_key``
naming another user's keypair is dropped rather than carried over. Users left
with keypairs but no marker — the state ``ON DELETE SET NULL`` produced — get
their oldest active keypair promoted, the same rule the original
``d3f8c74bf148`` migration used to populate ``main_access_key``.

Revision ID: a2f6b90c41d7
Revises: 2dccb3069031
Create Date: 2026-08-05 15:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a2f6b90c41d7"
down_revision = "2dccb3069031"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "keypairs",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.get_bind().execute(
        sa.text("""
            UPDATE keypairs
            SET is_default = true
            FROM users
            WHERE users.main_access_key = keypairs.access_key
              AND users.uuid = keypairs."user"
        """)
    )
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
    op.create_index(
        "uq_keypairs_is_default",
        "keypairs",
        ["user"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    op.drop_index("uq_keypairs_is_default", table_name="keypairs")
    op.drop_column("keypairs", "is_default")
