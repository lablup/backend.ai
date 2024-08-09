"""add keypair_resource_policy.max_concurrent_sftp_sessions column

Revision ID: 210c4d9be768
Revises: d6a02307a057
Create Date: 2023-05-24 11:14:03.460405

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "210c4d9be768"
down_revision = "d58a526bf837"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "keypair_resource_policies",
        sa.Column("max_concurrent_sftp_sessions", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade():
    op.drop_column(
        "keypair_resource_policies",
        "max_concurrent_sftp_sessions",
    )
