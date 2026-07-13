"""disable auto_assign for admin roles

An earlier backfill (eb9d9c018e85) set ``auto_assign = true`` for every
system-sourced role (``WHERE source = 'system'``). Admin roles are
system-sourced and were therefore swept into that backfill, which made them
auto-granted to every user who joins the owning scope — an unintended and
privilege-escalating behavior. Admin roles must never be auto-assigned.

This migration clears ``auto_assign`` for every role whose name ends with
``admin``. It is naturally idempotent: rows already at ``false`` are left
untouched by the ``auto_assign = true`` guard.

Revision ID: daf20413acda
Revises: f2b9a4c7e103
Create Date: 2026-07-13 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "daf20413acda"
down_revision = "f2b9a4c7e103"
# Part of: "26.4.8"
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
