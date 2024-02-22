"""add use_host_network column

Revision ID: c53397a490be
Revises: 5bce905c21e5
Create Date: 2022-10-25 17:02:31.709513

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.expression import false

# revision identifiers, used by Alembic.
revision = "c53397a490be"
down_revision = "5bce905c21e5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "kernels",
        sa.Column(
            "use_host_network", sa.BOOLEAN(), nullable=False, server_default=false(), default=False
        ),
    )
    op.add_column(
        "scaling_groups",
        sa.Column(
            "use_host_network", sa.BOOLEAN(), nullable=False, server_default=false(), default=False
        ),
    )


def downgrade():
    op.drop_column("kernels", "use_host_network")
    op.drop_column("scaling_groups", "use_host_network")
