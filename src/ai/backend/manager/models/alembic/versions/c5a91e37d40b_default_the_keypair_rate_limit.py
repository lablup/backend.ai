"""default the keypair rate limit in the column

``rate_limit`` was nullable with no default, so every create had to name a number
and the source kept one (``DEFAULT_KEYPAIR_RATE_LIMIT``) to name. A read then
turned the nulls it allowed into ``0``, a rate limit no caller intended.

Revision ID: c5a91e37d40b
Revises: b7e4c2058fa1
Create Date: 2026-08-21 10:05:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5a91e37d40b"
down_revision = "b7e4c2058fa1"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_DEFAULT_RATE_LIMIT = "10000"


def upgrade() -> None:
    op.execute(f"UPDATE keypairs SET rate_limit = {_DEFAULT_RATE_LIMIT} WHERE rate_limit IS NULL")
    op.alter_column(
        "keypairs",
        "rate_limit",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text(_DEFAULT_RATE_LIMIT),
    )


def downgrade() -> None:
    op.alter_column(
        "keypairs",
        "rate_limit",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )
