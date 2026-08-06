"""tighten the always-populated keypairs columns

Six columns are nullable in the schema and never null in practice, so every
reader has to handle a ``None`` that does not occur. Backfills the stragglers
with the value the application would have written and sets them NOT NULL.

``last_used``, ``ssh_public_key`` and ``ssh_private_key`` stay nullable — those
are genuinely empty for a keypair that has never been used or has no SSH key.
``created_at`` and ``updated_at`` were already tightened by ``2dccb3069031``.

``secret_key`` has no value that could be fabricated: a row without one is a
keypair nothing can authenticate with. If any exists the ALTER stops the
upgrade rather than inventing a secret.

Revision ID: e4a91c05df38
Revises: c8d51e7a3b62
Create Date: 2026-08-06 13:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4a91c05df38"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_DEFAULT_RATE_LIMIT = 10000

_TIGHTENED = (
    "user_id",
    "secret_key",
    "is_active",
    "is_admin",
    "rate_limit",
    "num_queries",
)


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("""
            UPDATE keypairs
            SET user_id = users.email
            FROM users
            WHERE users.uuid = keypairs."user" AND keypairs.user_id IS NULL
        """)
    )
    bind.execute(sa.text("UPDATE keypairs SET is_active = true WHERE is_active IS NULL"))
    bind.execute(sa.text("UPDATE keypairs SET is_admin = false WHERE is_admin IS NULL"))
    bind.execute(
        sa.text("UPDATE keypairs SET rate_limit = :limit WHERE rate_limit IS NULL"),
        {"limit": _DEFAULT_RATE_LIMIT},
    )
    bind.execute(sa.text("UPDATE keypairs SET num_queries = 0 WHERE num_queries IS NULL"))

    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=False)


def downgrade() -> None:
    for column in _TIGHTENED:
        op.alter_column("keypairs", column, nullable=True)
