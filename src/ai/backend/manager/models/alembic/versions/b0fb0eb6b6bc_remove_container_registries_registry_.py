"""Remove container_registries.registry_name length restriction

Revision ID: b0fb0eb6b6bc
Revises: d811b103dbfc
Create Date: 2025-10-29 10:38:05.866930

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b0fb0eb6b6bc"
down_revision = "d811b103dbfc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "container_registries",
        "registry_name",
        existing_type=sa.String(length=50),
        type_=sa.String(),
        existing_nullable=False,
        existing_server_default=None,
    )


def downgrade() -> None:
    op.alter_column(
        "container_registries",
        "registry_name",
        existing_type=sa.String(),
        type_=sa.String(length=50),
        existing_nullable=False,
        existing_server_default=None,
    )
