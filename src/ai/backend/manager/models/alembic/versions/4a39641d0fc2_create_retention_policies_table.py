"""create retention_policies table

Introduce the policy storage for DB record retention management (BEP-1063).
``retention_policies`` holds one row per ``RetentionCategory`` — the
admin-tunable ``retention_period`` + ``enabled`` knobs, plus a read-only
``last_swept_at`` observability field. The migration seeds one row per catalog
category with conservative defaults.

Revision ID: 4a39641d0fc2
Revises: d004f760adc7
Create Date: 2026-07-19

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "4a39641d0fc2"
down_revision = "d004f760adc7"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# (category, retention_period) — see BEP-1063 §3(a) default seed.
SEED_DATA = [
    ("logs", "1 year"),
    ("login", "1 year"),
    ("reconcile_history", "1 year"),
    ("roles_invitations", "1 year"),
    ("deployments", "1 year"),
    ("sessions", "1 year"),
    ("usage_records", "90 days"),
    ("usage_buckets", "2 years"),
]


def upgrade() -> None:
    op.create_table(
        "retention_policies",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("retention_period", sa.Interval(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_swept_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("category", name="uq_retention_policies_category"),
    )
    for category, period in SEED_DATA:
        op.execute(
            sa.text(
                "INSERT INTO retention_policies (category, retention_period)"
                " VALUES (:category, CAST(:period AS interval))"
                " ON CONFLICT (category) DO NOTHING"
            ).bindparams(category=category, period=period)
        )


def downgrade() -> None:
    op.drop_table("retention_policies")
