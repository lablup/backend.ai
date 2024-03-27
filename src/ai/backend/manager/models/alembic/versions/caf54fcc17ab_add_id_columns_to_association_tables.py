"""add_id_columns_to_association_tables

Revision ID: caf54fcc17ab
Revises: 8b2ec7e3d22a
Create Date: 2024-01-03 21:39:50.558724

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, metadata

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

    association_groups_users = sa.Table(
        "association_groups_users",
        metadata,
        sa.Column(
            "user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "group_id",
            GUID,
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        extend_existing=True,
    )

    sgroups_for_domains = sa.Table(
        "sgroups_for_domains",
        metadata,
        sa.Column(
            "scaling_group",
            sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "domain",
            sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        extend_existing=True,
    )

    sgroups_for_groups = sa.Table(
        "sgroups_for_groups",
        metadata,
        sa.Column(
            "scaling_group",
            sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "group",
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        extend_existing=True,
    )

    sgroups_for_keypairs = sa.Table(
        "sgroups_for_keypairs",
        metadata,
        sa.Column(
            "scaling_group",
            sa.ForeignKey("scaling_groups.name", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "access_key",
            sa.ForeignKey("keypairs.access_key", onupdate="CASCADE", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        extend_existing=True,
    )

    def drop_existing_pk(table: sa.sql.schema.Table) -> None:
        for const in table.constraints:
            if isinstance(const, sa.PrimaryKeyConstraint):
                op.drop_constraint(const.name, table.name, type_="primary")
                break

    drop_existing_pk(association_groups_users)
    drop_existing_pk(sgroups_for_domains)
    drop_existing_pk(sgroups_for_groups)
    drop_existing_pk(sgroups_for_keypairs)

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
