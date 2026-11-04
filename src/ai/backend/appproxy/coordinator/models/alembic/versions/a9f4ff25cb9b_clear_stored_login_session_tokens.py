"""clear stored login session tokens

Revision ID: a9f4ff25cb9b
Revises: a1b2c3d4e5f6
Create Date: 2026-11-04 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a9f4ff25cb9b"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE tokens SET login_session_token = NULL WHERE login_session_token IS NOT NULL"
        )
    )


def downgrade() -> None:
    # The cleared values cannot be restored.
    pass
