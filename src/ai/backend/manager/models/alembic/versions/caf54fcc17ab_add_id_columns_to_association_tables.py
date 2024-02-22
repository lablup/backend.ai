"""add_id_columns_to_association_tables

Revision ID: caf54fcc17ab
Revises: 8b2ec7e3d22a
Create Date: 2024-01-03 21:39:50.558724

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "caf54fcc17ab"
down_revision = "8b2ec7e3d22a"
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

    def drop_existing_pk(idx: str, table: str):
        try:
            op.drop_constraint(idx, table, type_="primary")
        except sa.exc.ProgrammingError:
            # Skip dropping if the table has no primary key
            pass

    drop_existing_pk("pk_association_groups_users", "association_groups_users")
    drop_existing_pk("pk_sgroups_for_domains", "sgroups_for_domains")
    drop_existing_pk("pk_sgroups_for_groups", "sgroups_for_groups")
    drop_existing_pk("pk_sgroups_for_keypairs", "sgroups_for_keypairs")

    op.create_primary_key("pk_association_groups_users", "association_groups_users", ["id"])
    op.create_primary_key("pk_sgroups_for_domains", "sgroups_for_domains", ["id"])
    op.create_primary_key("pk_sgroups_for_groups", "sgroups_for_groups", ["id"])
    op.create_primary_key("pk_sgroups_for_keypairs", "sgroups_for_keypairs", ["id"])


def downgrade():
    op.drop_constraint("pk_association_groups_users", "association_groups_users", type_="primary")
    op.drop_constraint("pk_sgroups_for_domains", "sgroups_for_domains", type_="primary")
    op.drop_constraint("pk_sgroups_for_groups", "sgroups_for_groups", type_="primary")
    op.drop_constraint("pk_sgroups_for_keypairs", "sgroups_for_keypairs", type_="primary")

    op.drop_column("sgroups_for_keypairs", "id")
    op.drop_column("sgroups_for_groups", "id")
    op.drop_column("sgroups_for_domains", "id")
    op.drop_column("association_groups_users", "id")

    op.create_primary_key(
        "pk_association_groups_users", "association_groups_users", ["user_id", "group_id"]
    )
    op.create_primary_key(
        "pk_sgroups_for_domains", "sgroups_for_domains", ["scaling_group", "domain"]
    )
    op.create_primary_key("pk_sgroups_for_groups", "sgroups_for_groups", ["scaling_group", "group"])
    op.create_primary_key(
        "pk_sgroups_for_keypairs", "sgroups_for_keypairs", ["scaling_group", "access_key"]
    )
