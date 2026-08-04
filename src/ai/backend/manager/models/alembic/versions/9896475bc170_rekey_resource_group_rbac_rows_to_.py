"""rekey resource group rbac rows to resource group uuid

Resource groups were keyed by name in the ``sgroups_for_*`` mapping tables
and in the legacy RBAC tables (``association_scopes_entities``,
``permissions``), while the RBAC scope chain keys them by ``scaling_groups.id``.
This migration unifies the resource-group key on the row UUID:

- ``sgroups_for_domains`` / ``sgroups_for_groups`` / ``sgroups_for_keypairs``:
  the ``scaling_group`` name FK column is replaced by a ``scaling_group_id``
  FK column referencing ``scaling_groups.id``.
- ``association_scopes_entities`` rows keyed by a resource-group name (as
  entity or as scope) are converted to the canonical string form of
  ``scaling_groups.id``; rows referencing deleted resource groups are dropped.
- ``permissions`` rows with a resource-group scope are converted likewise.

Name-keyed rows are matched via a join on ``scaling_groups.name`` (converted
rows no longer match), converted rows that would collide with an existing
UUID-keyed duplicate are dropped instead, and the remaining non-UUID-keyed
rows are removed as dangling.

Revision ID: 9896475bc170
Revises: 9fbeda8995ff
Create Date: 2026-08-03 21:14:37.626627

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "9896475bc170"
down_revision = "9fbeda8995ff"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# (table, sibling unique column, unique constraint name)
_MAPPING_TABLES = (
    ("sgroups_for_domains", "domain", "uq_sgroup_domain"),
    ("sgroups_for_groups", "group", "uq_sgroup_ugroup"),
    ("sgroups_for_keypairs", "access_key", "uq_sgroup_akey"),
)


def _rekey_mapping_tables_to_uuid() -> None:
    conn = op.get_bind()
    for table, sibling, uq_name in _MAPPING_TABLES:
        op.add_column(table, sa.Column("scaling_group_id", GUID(), nullable=True))
        conn.execute(
            sa.text(f"""
                UPDATE {table} t
                SET scaling_group_id = sg.id
                FROM scaling_groups sg
                WHERE t.scaling_group = sg.name
            """)
        )
        op.alter_column(table, "scaling_group_id", nullable=False)
        op.drop_constraint(f"fk_{table}_scaling_group_scaling_groups", table, type_="foreignkey")
        op.drop_constraint(uq_name, table, type_="unique")
        op.drop_index(f"ix_{table}_scaling_group", table_name=table)
        op.drop_column(table, "scaling_group")
        op.create_unique_constraint(uq_name, table, ["scaling_group_id", sibling])
        op.create_index(f"ix_{table}_scaling_group_id", table, ["scaling_group_id"])
        op.create_foreign_key(
            f"fk_{table}_scaling_group_id_scaling_groups",
            table,
            "scaling_groups",
            ["scaling_group_id"],
            ["id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        )


def _rekey_mapping_tables_to_name() -> None:
    conn = op.get_bind()
    for table, sibling, uq_name in _MAPPING_TABLES:
        op.add_column(table, sa.Column("scaling_group", sa.String(length=64), nullable=True))
        conn.execute(
            sa.text(f"""
                UPDATE {table} t
                SET scaling_group = sg.name
                FROM scaling_groups sg
                WHERE t.scaling_group_id = sg.id
            """)
        )
        op.alter_column(table, "scaling_group", nullable=False)
        op.drop_constraint(f"fk_{table}_scaling_group_id_scaling_groups", table, type_="foreignkey")
        op.drop_constraint(uq_name, table, type_="unique")
        op.drop_index(f"ix_{table}_scaling_group_id", table_name=table)
        op.drop_column(table, "scaling_group_id")
        op.create_unique_constraint(uq_name, table, ["scaling_group", sibling])
        op.create_index(f"ix_{table}_scaling_group", table, ["scaling_group"])
        op.create_foreign_key(
            f"fk_{table}_scaling_group_scaling_groups",
            table,
            "scaling_groups",
            ["scaling_group"],
            ["name"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        )


def _rekey_rbac_rows_to_uuid() -> None:
    conn = op.get_bind()
    # association_scopes_entities: resource group as entity.
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET entity_id = sg.id::text
            FROM scaling_groups sg
            WHERE ase.entity_type = 'resource_group'
              AND ase.entity_id = sg.name
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = ase.scope_type
                    AND dup.scope_id = ase.scope_id
                    AND dup.entity_id = sg.id::text
              )
        """)
    )
    # Leftover rows are either duplicates of already-converted rows or
    # dangling references to deleted resource groups.
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            WHERE ase.entity_type = 'resource_group'
              AND NOT EXISTS (
                  SELECT 1 FROM scaling_groups sg
                  WHERE sg.id::text = ase.entity_id
              )
        """)
    )
    # association_scopes_entities: resource group as scope.
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET scope_id = sg.id::text
            FROM scaling_groups sg
            WHERE ase.scope_type = 'resource_group'
              AND ase.scope_id = sg.name
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = 'resource_group'
                    AND dup.scope_id = sg.id::text
                    AND dup.entity_id = ase.entity_id
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            WHERE ase.scope_type = 'resource_group'
              AND NOT EXISTS (
                  SELECT 1 FROM scaling_groups sg
                  WHERE sg.id::text = ase.scope_id
              )
        """)
    )
    # permissions: resource group as scope.
    conn.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_id = sg.id::text
            FROM scaling_groups sg
            WHERE p.scope_type = 'resource_group'
              AND p.scope_id = sg.name
              AND NOT EXISTS (
                  SELECT 1 FROM permissions dup
                  WHERE dup.role_id = p.role_id
                    AND dup.scope_type = 'resource_group'
                    AND dup.scope_id = sg.id::text
                    AND dup.entity_type = p.entity_type
                    AND dup.operation = p.operation
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            WHERE p.scope_type = 'resource_group'
              AND NOT EXISTS (
                  SELECT 1 FROM scaling_groups sg
                  WHERE sg.id::text = p.scope_id
              )
        """)
    )


def _rekey_rbac_rows_to_name() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET entity_id = sg.name
            FROM scaling_groups sg
            WHERE ase.entity_type = 'resource_group'
              AND ase.entity_id = sg.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = ase.scope_type
                    AND dup.scope_id = ase.scope_id
                    AND dup.entity_id = sg.name
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING scaling_groups sg
            WHERE ase.entity_type = 'resource_group'
              AND ase.entity_id = sg.id::text
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET scope_id = sg.name
            FROM scaling_groups sg
            WHERE ase.scope_type = 'resource_group'
              AND ase.scope_id = sg.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = 'resource_group'
                    AND dup.scope_id = sg.name
                    AND dup.entity_id = ase.entity_id
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING scaling_groups sg
            WHERE ase.scope_type = 'resource_group'
              AND ase.scope_id = sg.id::text
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_id = sg.name
            FROM scaling_groups sg
            WHERE p.scope_type = 'resource_group'
              AND p.scope_id = sg.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM permissions dup
                  WHERE dup.role_id = p.role_id
                    AND dup.scope_type = 'resource_group'
                    AND dup.scope_id = sg.name
                    AND dup.entity_type = p.entity_type
                    AND dup.operation = p.operation
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING scaling_groups sg
            WHERE p.scope_type = 'resource_group'
              AND p.scope_id = sg.id::text
        """)
    )


def upgrade() -> None:
    _rekey_mapping_tables_to_uuid()
    _rekey_rbac_rows_to_uuid()


def downgrade() -> None:
    _rekey_rbac_rows_to_name()
    _rekey_mapping_tables_to_name()
