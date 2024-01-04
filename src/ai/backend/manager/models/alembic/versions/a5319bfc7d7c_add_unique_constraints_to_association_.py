"""add_unique_constraints_to_association_tables

Revision ID: a5319bfc7d7c
Revises: caf54fcc17ab
Create Date: 2024-01-03 21:43:31.208183

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, mapper_registry

# revision identifiers, used by Alembic.
revision = "a5319bfc7d7c"
down_revision = "caf54fcc17ab"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    association_groups_users = sa.Table(
        "association_groups_users",
        mapper_registry.metadata,
        sa.Column(
            "id",
            GUID,
            primary_key=True,
            nullable=False,
        ),
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
        sa.UniqueConstraint("user_id", "group_id", name="uq_association_user_id_group_id"),
        extend_existing=True,
    )

    sgroups_for_domains = sa.Table(
        "sgroups_for_domains",
        mapper_registry.metadata,
        sa.Column(
            "id",
            GUID,
            primary_key=True,
            nullable=False,
        ),
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
        mapper_registry.metadata,
        sa.Column(
            "id",
            GUID,
            primary_key=True,
            nullable=False,
        ),
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
        mapper_registry.metadata,
        sa.Column(
            "id",
            GUID,
            primary_key=True,
            nullable=False,
        ),
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

    def ensure_unique(table, field_1: str, field_2: str) -> None:
        # Leave only one duplicate record and delete all of it
        t1 = table.alias("t1")
        t2 = table.alias("t2")
        subq = (
            sa.select([t1.c.id])
            .where(t1.c[field_1] == t2.c[field_1])
            .where(t1.c[field_2] == t2.c[field_2])
            .where(t1.c.id > t2.c.id)
        )
        delete_stmt = sa.delete(table).where(table.c.id.in_(subq))
        conn.execute(delete_stmt)

    ensure_unique(association_groups_users, "user_id", "group_id")
    ensure_unique(sgroups_for_domains, "scaling_group", "domain")
    ensure_unique(sgroups_for_groups, "scaling_group", "group")
    ensure_unique(sgroups_for_keypairs, "scaling_group", "access_key")

    op.create_unique_constraint(
        "uq_association_user_id_group_id", "association_groups_users", ["user_id", "group_id"]
    )
    op.create_unique_constraint(
        "uq_sgroup_domain", "sgroups_for_domains", ["scaling_group", "domain"]
    )
    op.create_unique_constraint(
        "uq_sgroup_ugroup", "sgroups_for_groups", ["scaling_group", "group"]
    )
    op.create_unique_constraint(
        "uq_sgroup_akey", "sgroups_for_keypairs", ["scaling_group", "access_key"]
    )


def downgrade():
    op.drop_constraint(
        "uq_association_user_id_group_id", "association_groups_users", type_="unique"
    )
    op.drop_constraint("uq_sgroup_domain", "sgroups_for_domains", type_="unique")
    op.drop_constraint("uq_sgroup_ugroup", "sgroups_for_groups", type_="unique")
    op.drop_constraint("uq_sgroup_akey", "sgroups_for_keypairs", type_="unique")
