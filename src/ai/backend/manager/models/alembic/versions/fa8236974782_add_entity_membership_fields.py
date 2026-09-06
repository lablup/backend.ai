"""cap membership edges by rows

Revision ID: fa8236974782
Revises: b44c240c7680
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "fa8236974782"
down_revision = "b44c240c7680"
branch_labels = None
depends_on = None

_BITS = (1, 2, 4, 8, 16)


def upgrade() -> None:
    # The edge gets its own id; the node pair stays unique.
    op.add_column(
        "entity_memberships",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
    )
    op.drop_constraint("pk_entity_memberships", "entity_memberships", type_="primary")
    op.create_primary_key("pk_entity_memberships", "entity_memberships", ["id"])
    op.create_unique_constraint(
        "uq_entity_memberships_edge",
        "entity_memberships",
        ["virtual_entity_id", "member_entity_id"],
    )
    op.create_table(
        "entity_membership_caps",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("membership_id", GUID(), nullable=False),
        sa.Column("permission", sa.SmallInteger(), nullable=False),
        sa.Column("all_fields", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "permission > 0 AND (permission & (permission - 1)) = 0",
            name="ck_entity_membership_caps_single_bit",
        ),
        sa.CheckConstraint(
            "all_fields OR permission IN (1, 2)", name="ck_entity_membership_caps_field_scope"
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["entity_memberships.id"],
            name=op.f("fk_entity_membership_caps_membership_id_entity_memberships"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entity_membership_caps")),
        sa.UniqueConstraint("membership_id", "permission", name="uq_entity_membership_caps_bit"),
    )
    op.create_table(
        "entity_membership_fields",
        sa.Column("cap_id", GUID(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.CheckConstraint("path <> ''", name="ck_entity_membership_fields_path"),
        sa.ForeignKeyConstraint(
            ["cap_id"],
            ["entity_membership_caps.id"],
            name=op.f("fk_entity_membership_fields_cap_id_entity_membership_caps"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("cap_id", "path", name=op.f("pk_entity_membership_fields")),
    )
    # The inline mask becomes one cap row per bit; a NULL mask is a belonging edge.
    op.add_column(
        "entity_memberships",
        sa.Column("capped", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute(
        sa.text("UPDATE entity_memberships SET capped = TRUE WHERE permission_cap IS NOT NULL")
    )
    for bit in _BITS:
        op.execute(
            sa.text(
                "INSERT INTO entity_membership_caps (membership_id, permission, all_fields)"
                f" SELECT id, {bit}, TRUE FROM entity_memberships WHERE (permission_cap & {bit}) <> 0"
            )
        )
    op.drop_index("ix_entity_memberships_entity", table_name="entity_memberships")
    op.drop_column("entity_memberships", "permission_cap")
    op.create_index(
        "ix_entity_memberships_entity",
        "entity_memberships",
        ["member_entity_id"],
        unique=False,
        postgresql_include=["virtual_entity_id", "capped"],
    )


def downgrade() -> None:
    op.drop_index("ix_entity_memberships_entity", table_name="entity_memberships")
    op.add_column(
        "entity_memberships",
        sa.Column("permission_cap", sa.SmallInteger(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE entity_memberships em SET permission_cap = COALESCE("
            " (SELECT SUM(permission) FROM entity_membership_caps c"
            "  WHERE c.membership_id = em.id AND c.all_fields), 0)"
            " WHERE em.capped"
        )
    )
    op.create_index(
        "ix_entity_memberships_entity",
        "entity_memberships",
        ["member_entity_id"],
        unique=False,
        postgresql_include=["virtual_entity_id", "permission_cap"],
    )
    op.drop_column("entity_memberships", "capped")
    op.drop_table("entity_membership_fields")
    op.drop_table("entity_membership_caps")
    op.drop_constraint("uq_entity_memberships_edge", "entity_memberships", type_="unique")
    op.drop_constraint("pk_entity_memberships", "entity_memberships", type_="primary")
    op.create_primary_key(
        "pk_entity_memberships", "entity_memberships", ["virtual_entity_id", "member_entity_id"]
    )
    op.drop_column("entity_memberships", "id")
