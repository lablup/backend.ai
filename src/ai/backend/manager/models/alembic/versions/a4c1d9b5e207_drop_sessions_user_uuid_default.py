"""drop the server default of sessions.user_uuid

Revision ID: a4c1d9b5e207
Revises: 8f3b1c7ad204
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "a4c1d9b5e207"
down_revision = "8f3b1c7ad204"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE sessions ALTER COLUMN user_uuid DROP DEFAULT"))


def downgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE sessions ALTER COLUMN user_uuid SET DEFAULT uuid_generate_v4()")
    )
