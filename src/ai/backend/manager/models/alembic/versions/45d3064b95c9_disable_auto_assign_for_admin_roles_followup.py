"""disable auto_assign for admin roles (main-head follow-up)

Duplicate of daf20413acda for the main branch. daf20413acda is inserted into
the chain right after f2b9a4c7e103, so databases already migrated past that
point (i.e. at the current main head) would never replay it. This follow-up
re-applies the same correction at the main head so those databases also get
it. It performs the identical, idempotent UPDATE and is a no-op on databases
that already ran daf20413acda.

Revision ID: 45d3064b95c9
Revises: 2ec0aa5a19cf
Create Date: 2026-07-13 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "45d3064b95c9"
down_revision = "2ec0aa5a19cf"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE roles SET auto_assign = false WHERE name LIKE :pattern AND auto_assign = true"
        ).bindparams(pattern="%admin")
    )


def downgrade() -> None:
    # No-op: re-enabling auto_assign for admin roles would reintroduce the
    # privilege-escalation behavior this migration fixes, and the pre-migration
    # value cannot be reconstructed. Leaving auto_assign = false is safe.
    pass
