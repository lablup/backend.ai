"""add_id_columns_to_association_tables

Revision ID: caf54fcc17ab
Revises: d3f8c74bf148
Create Date: 2024-01-03 21:39:50.558724

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "caf54fcc17ab"
down_revision = "d3f8c74bf148"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "association_groups_users",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.add_column(
        "sgroups_for_domains",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.add_column(
        "sgroups_for_groups",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.add_column(
        "sgroups_for_keypairs",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )


def downgrade():
    op.drop_column("sgroups_for_keypairs", "id")
    op.drop_column("sgroups_for_groups", "id")
    op.drop_column("sgroups_for_domains", "id")
    op.drop_column("association_groups_users", "id")
