"""add ``id`` UUID column to ``scaling_groups`` and demote ``name`` to unique

Adds a UUID ``id`` column as the new primary key of the ``scaling_groups``
table. The legacy ``name`` column becomes a UNIQUE column so existing
foreign-key references continue to function.

PostgreSQL tracks foreign-key dependencies on the primary-key index, so the
swap requires temporarily dropping and recreating every FK that points to
``scaling_groups.name``. The FK definitions are restored with identical
semantics (column, target column, and ON UPDATE/DELETE rules unchanged).

Revision ID: b2d4f6e8c1a3
Revises: a1c3e5d7b9f2
Create Date: 2026-05-15

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b2d4f6e8c1a3"
down_revision = "a1c3e5d7b9f2"
branch_labels = None
depends_on = None


# (referencing_table, fk_constraint_name, fk_column, on_update, on_delete)
_SCALING_GROUP_FK_REFS: tuple[tuple[str, str, str, str | None, str | None], ...] = (
    ("agents", "fk_agents_scaling_group_scaling_groups", "scaling_group", None, None),
    (
        "endpoints",
        "fk_endpoints_resource_group_scaling_groups",
        "resource_group",
        None,
        "RESTRICT",
    ),
    ("kernels", "fk_kernels_scaling_group_scaling_groups", "scaling_group", None, None),
    (
        "sessions",
        "fk_sessions_scaling_group_name_scaling_groups",
        "scaling_group_name",
        None,
        None,
    ),
    (
        "sgroups_for_domains",
        "fk_sgroups_for_domains_scaling_group_scaling_groups",
        "scaling_group",
        "CASCADE",
        "CASCADE",
    ),
    (
        "sgroups_for_groups",
        "fk_sgroups_for_groups_scaling_group_scaling_groups",
        "scaling_group",
        "CASCADE",
        "CASCADE",
    ),
    (
        "sgroups_for_keypairs",
        "fk_sgroups_for_keypairs_scaling_group_scaling_groups",
        "scaling_group",
        "CASCADE",
        "CASCADE",
    ),
)


def upgrade() -> None:
    op.add_column(
        "scaling_groups",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )

    for table, fk_name, _column, _on_update, _on_delete in _SCALING_GROUP_FK_REFS:
        op.drop_constraint(fk_name, table, type_="foreignkey")

    op.create_unique_constraint("uq_scaling_groups_name", "scaling_groups", ["name"])
    op.drop_constraint("pk_scaling_groups", "scaling_groups", type_="primary")
    op.create_primary_key("pk_scaling_groups", "scaling_groups", ["id"])

    for table, fk_name, column, on_update, on_delete in _SCALING_GROUP_FK_REFS:
        op.create_foreign_key(
            fk_name,
            table,
            "scaling_groups",
            [column],
            ["name"],
            onupdate=on_update,
            ondelete=on_delete,
        )


def downgrade() -> None:
    for table, fk_name, _column, _on_update, _on_delete in _SCALING_GROUP_FK_REFS:
        op.drop_constraint(fk_name, table, type_="foreignkey")

    op.drop_constraint("pk_scaling_groups", "scaling_groups", type_="primary")
    op.drop_constraint("uq_scaling_groups_name", "scaling_groups", type_="unique")
    op.create_primary_key("pk_scaling_groups", "scaling_groups", ["name"])
    op.drop_column("scaling_groups", "id")

    for table, fk_name, column, on_update, on_delete in _SCALING_GROUP_FK_REFS:
        op.create_foreign_key(
            fk_name,
            table,
            "scaling_groups",
            [column],
            ["name"],
            onupdate=on_update,
            ondelete=on_delete,
        )
