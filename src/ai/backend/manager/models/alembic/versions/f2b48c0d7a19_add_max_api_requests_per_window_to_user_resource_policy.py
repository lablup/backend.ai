"""add max_api_requests_per_window to user_resource_policy

NULL means unlimited; integer N means at most N API requests are allowed per
user within the rate limit window. Replaces keypairs.rate_limit as the source
of the per-user API rate limit, which is now deprecated and ignored.

Revision ID: f2b48c0d7a19
Revises: d4e6f8a0b2c3
Create Date: 2026-08-14 15:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2b48c0d7a19"
down_revision = "d4e6f8a0b2c3"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user_resource_policies")}
    if "max_api_requests_per_window" not in cols:
        op.add_column(
            "user_resource_policies",
            sa.Column("max_api_requests_per_window", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user_resource_policies")}
    if "max_api_requests_per_window" in cols:
        op.drop_column("user_resource_policies", "max_api_requests_per_window")
