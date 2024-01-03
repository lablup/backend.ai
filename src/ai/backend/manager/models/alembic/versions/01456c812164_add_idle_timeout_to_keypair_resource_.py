"""add-idle-timeout-to-keypair-resource-policy

Revision ID: 01456c812164
Revises: dbc1e053b880
Create Date: 2019-02-22 22:16:47.685740

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "01456c812164"
down_revision = "dbc1e053b880"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "keypair_resource_policies",
        sa.Column("idle_timeout", sa.BigInteger(), nullable=False, server_default="1800"),
    )
    op.alter_column("keypair_resource_policies", "idle_timeout", server_default=None)


def downgrade():
    op.drop_column("keypair_resource_policies", "idle_timeout")
