"""add max_concurrent_logins to user_resource_policy

NULL means unlimited; integer N means at most N concurrent authenticated login
sessions are allowed per user. This is distinct from
keypair_resource_policies.max_concurrent_sessions, which limits the number of
compute sessions rather than login sessions.

Revision ID: 689f66507280
Revises: 9dc6609c92ce
Create Date: 2026-04-07

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "689f66507280"
down_revision = "9dc6609c92ce"
# Part of: 26.3.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user_resource_policies")}
    if "max_concurrent_logins" not in cols:
        op.add_column(
            "user_resource_policies",
            sa.Column("max_concurrent_logins", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user_resource_policies")}
    if "max_concurrent_logins" in cols:
        op.drop_column("user_resource_policies", "max_concurrent_logins")
