"""seed retention_policies disabled by default

Make DB record retention opt-in (BEP-1063 follow-up). The initial table
migration ``4a39641d0fc2`` seeded eight category rows without an explicit
``enabled`` value, so they inherited the column default ``true`` and retention
swept automatically. Flip the column default to ``false`` and disable the seeded
rows so nothing is purged until a super-admin turns a category on.

Revision ID: b3e8f1a24c76
Revises: ea422739665b
Create Date: 2026-07-21

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3e8f1a24c76"
down_revision = "ea422739665b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

SEED_CATEGORIES = [
    "logs",
    "login",
    "reconcile_history",
    "roles_invitations",
    "deployments",
    "sessions",
    "usage_records",
    "usage_buckets",
]


def upgrade() -> None:
    op.alter_column("retention_policies", "enabled", server_default=sa.false())
    op.execute(
        sa.text(
            "UPDATE retention_policies SET enabled = false WHERE category = ANY(:categories)"
        ).bindparams(categories=SEED_CATEGORIES)
    )


def downgrade() -> None:
    # The ``enabled`` flag is operator-managed policy state; do not flip rows
    # back to enabled here — only restore the previous column default.
    op.alter_column("retention_policies", "enabled", server_default=sa.true())
