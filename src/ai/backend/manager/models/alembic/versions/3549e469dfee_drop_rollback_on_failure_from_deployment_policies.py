"""drop rollback_on_failure from deployment_policies

Revision ID: 3549e469dfee
Revises: 30c8308738ee
Create Date: 2026-03-23

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3549e469dfee"
down_revision = "30c8308738ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("deployment_policies", "rollback_on_failure")


def downgrade() -> None:
    op.add_column(
        "deployment_policies",
        sa.Column(
            "rollback_on_failure",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
