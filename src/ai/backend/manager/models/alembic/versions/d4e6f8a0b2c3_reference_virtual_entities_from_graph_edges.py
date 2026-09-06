"""reference virtual entities from graph edges

Revision ID: d4e6f8a0b2c3
Revises: c2d4e6f8a0b1
Create Date: 2026-09-02 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d4e6f8a0b2c3"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c2d4e6f8a0b1"
branch_labels = None
depends_on = None

# (table, type column, id column, new FK column) for the two graph edges that named an
# entity as a (type, id) pair. permissions / field_permissions keep their pair: they
# must name the global scope, which is no entity. entity_labels / entity_invitations
# keep theirs: they are attributes of an entity, not graph edges.
_PAIRS = (
    ("entity_memberships", "entity_type", "entity_id", "member_entity_id"),
    ("scope_bindings", "scope_type", "scope_id", "scope_entity_id"),
)


def _provision_missing_nodes(table: str, type_col: str, id_col: str) -> None:
    op.execute(
        f"INSERT INTO virtual_entities (id, entity_type, entity_id) "
        f"SELECT uuid_generate_v4(), {type_col}, {id_col} FROM {table} "
        f"GROUP BY {type_col}, {id_col} "
        f"ON CONFLICT (entity_type, entity_id) DO NOTHING"
    )


def _backfill_fk(table: str, type_col: str, id_col: str, fk_col: str) -> None:
    op.execute(
        f"UPDATE {table} t SET {fk_col} = v.id FROM virtual_entities v "
        f"WHERE v.entity_type = t.{type_col} AND v.entity_id = t.{id_col}"
    )


def _restore_pair(table: str, type_col: str, id_col: str, fk_col: str) -> None:
    op.execute(
        f"UPDATE {table} t SET {type_col} = v.entity_type, {id_col} = v.entity_id "
        f"FROM virtual_entities v WHERE v.id = t.{fk_col}"
    )


def upgrade() -> None:
    for table, type_col, id_col, _ in _PAIRS:
        _provision_missing_nodes(table, type_col, id_col)

    # entity_memberships: (entity_type, entity_id) -> member_entity_id
    op.add_column("entity_memberships", sa.Column("member_entity_id", GUID(), nullable=True))
    _backfill_fk("entity_memberships", "entity_type", "entity_id", "member_entity_id")
    op.alter_column("entity_memberships", "member_entity_id", nullable=False)
    op.execute("ALTER TABLE entity_memberships DROP CONSTRAINT pk_entity_memberships")
    op.drop_index("ix_entity_memberships_entity", table_name="entity_memberships")
    op.drop_column("entity_memberships", "entity_id")
    op.drop_column("entity_memberships", "entity_type")
    op.create_primary_key(
        "pk_entity_memberships", "entity_memberships", ["virtual_entity_id", "member_entity_id"]
    )
    op.create_foreign_key(
        "fk_entity_memberships_member_entity_id_virtual_entities",
        "entity_memberships",
        "virtual_entities",
        ["member_entity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        "CREATE INDEX ix_entity_memberships_entity ON entity_memberships (member_entity_id) "
        "INCLUDE (virtual_entity_id, permission_cap)"
    )

    # scope_bindings: (scope_type, scope_id) -> scope_entity_id
    op.add_column("scope_bindings", sa.Column("scope_entity_id", GUID(), nullable=True))
    _backfill_fk("scope_bindings", "scope_type", "scope_id", "scope_entity_id")
    op.alter_column("scope_bindings", "scope_entity_id", nullable=False)
    op.execute("ALTER TABLE scope_bindings DROP CONSTRAINT pk_scope_bindings")
    op.drop_index("ix_scope_bindings_scope", table_name="scope_bindings")
    op.drop_index("ix_scope_bindings_virtual_entity", table_name="scope_bindings")
    op.drop_column("scope_bindings", "scope_id")
    op.drop_column("scope_bindings", "scope_type")
    op.create_primary_key(
        "pk_scope_bindings", "scope_bindings", ["virtual_entity_id", "scope_entity_id"]
    )
    op.create_foreign_key(
        "fk_scope_bindings_scope_entity_id_virtual_entities",
        "scope_bindings",
        "virtual_entities",
        ["scope_entity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_scope_bindings_scope", "scope_bindings", ["scope_entity_id"])
    op.execute(
        "CREATE INDEX ix_scope_bindings_virtual_entity ON scope_bindings (virtual_entity_id) "
        "INCLUDE (scope_entity_id, permission_cap)"
    )


def downgrade() -> None:
    # scope_bindings
    op.drop_index("ix_scope_bindings_virtual_entity", table_name="scope_bindings")
    op.drop_index("ix_scope_bindings_scope", table_name="scope_bindings")
    op.drop_constraint(
        "fk_scope_bindings_scope_entity_id_virtual_entities", "scope_bindings", type_="foreignkey"
    )
    op.execute("ALTER TABLE scope_bindings DROP CONSTRAINT pk_scope_bindings")
    op.add_column("scope_bindings", sa.Column("scope_type", sa.String(length=32), nullable=True))
    op.add_column("scope_bindings", sa.Column("scope_id", GUID(), nullable=True))
    _restore_pair("scope_bindings", "scope_type", "scope_id", "scope_entity_id")
    op.alter_column("scope_bindings", "scope_type", nullable=False)
    op.alter_column("scope_bindings", "scope_id", nullable=False)
    op.drop_column("scope_bindings", "scope_entity_id")
    op.create_primary_key(
        "pk_scope_bindings", "scope_bindings", ["virtual_entity_id", "scope_type", "scope_id"]
    )
    op.create_index("ix_scope_bindings_scope", "scope_bindings", ["scope_type", "scope_id"])
    op.execute(
        "CREATE INDEX ix_scope_bindings_virtual_entity ON scope_bindings (virtual_entity_id) "
        "INCLUDE (scope_type, scope_id, permission_cap)"
    )

    # entity_memberships
    op.drop_index("ix_entity_memberships_entity", table_name="entity_memberships")
    op.drop_constraint(
        "fk_entity_memberships_member_entity_id_virtual_entities",
        "entity_memberships",
        type_="foreignkey",
    )
    op.execute("ALTER TABLE entity_memberships DROP CONSTRAINT pk_entity_memberships")
    op.add_column(
        "entity_memberships", sa.Column("entity_type", sa.String(length=32), nullable=True)
    )
    op.add_column("entity_memberships", sa.Column("entity_id", GUID(), nullable=True))
    _restore_pair("entity_memberships", "entity_type", "entity_id", "member_entity_id")
    op.alter_column("entity_memberships", "entity_type", nullable=False)
    op.alter_column("entity_memberships", "entity_id", nullable=False)
    op.drop_column("entity_memberships", "member_entity_id")
    op.create_primary_key(
        "pk_entity_memberships",
        "entity_memberships",
        ["virtual_entity_id", "entity_type", "entity_id"],
    )
    op.execute(
        "CREATE INDEX ix_entity_memberships_entity ON entity_memberships (entity_type, entity_id) "
        "INCLUDE (virtual_entity_id, permission_cap)"
    )
