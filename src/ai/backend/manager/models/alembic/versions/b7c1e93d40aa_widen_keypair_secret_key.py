"""Widen keypairs.secret_key to text for encrypted storage

An encrypted secret key does not fit in 40 characters, and its length follows the key
provider that wrote it. No data is converted: an existing row carries no marker and is
therefore read as plaintext.

Revision ID: b7c1e93d40aa
Revises: d7a2f4c86b13
Create Date: 2026-08-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c1e93d40aa"
down_revision = "d7a2f4c86b13"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_MAX_LEGACY_LENGTH = 40


def upgrade() -> None:
    # varchar to text is binary coercible, so this rewrites no rows. Re-running it on a
    # column that is already text is a no-op.
    op.execute(sa.text("ALTER TABLE keypairs ALTER COLUMN secret_key TYPE text"))


def downgrade() -> None:
    # PostgreSQL refuses this while any encrypted value is stored, which is the intended
    # guard: converting those rows back to plaintext comes first.
    op.execute(
        sa.text(f"ALTER TABLE keypairs ALTER COLUMN secret_key TYPE varchar({_MAX_LEGACY_LENGTH})")
    )
