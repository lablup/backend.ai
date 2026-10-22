"""Add the vfolder auto-mount table and grant the seed roles on it.

The grants are what the role files now state, written to the presets and to every
role made from them, so an installation seeded before this reaches the new entity
the way a fresh one does.

Revision ID: 456a338e7c3a
Revises: 945c2f111c6b
Create Date: 2026-10-22

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "456a338e7c3a"
down_revision = "945c2f111c6b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_ENTITY_TYPE: Final[str] = "vfolder_auto_mount"

_READ: Final[int] = 1
_FULL: Final[tuple[int, ...]] = (1, 2, 4, 8, 16)

# The bits each preset is granted, as (preset id, bits).
_GRANTS: Final[tuple[tuple[str, tuple[int, ...]], ...]] = (
    # domain_admin
    ("9ebf4f57-9e67-5631-997a-d2d79cc3815f", _FULL),
    # project_admin
    ("22c4db03-24aa-5ff8-b5a9-64b2a2182413", _FULL),
    # project_member
    ("06057849-3534-546f-b74c-b79d5d3ecf5e", (_READ,)),
)


def _grant(conn: sa.engine.Connection) -> None:
    params = [
        {"preset_id": preset_id, "entity_type": _ENTITY_TYPE, "permission": bit}
        for preset_id, bits in _GRANTS
        for bit in bits
    ]
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (role_preset_id, entity_type, permission)
            SELECT p.id, :entity_type, :permission
            FROM role_presets p
            WHERE p.id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """),
        params,
    )
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT r.id, :entity_type, :permission
            FROM roles r
            WHERE r.role_preset_id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """),
        params,
    )


def _revoke(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type = :entity_type").bindparams(
            entity_type=_ENTITY_TYPE
        )
    )
    conn.execute(
        sa.text("DELETE FROM role_permission_presets WHERE entity_type = :entity_type").bindparams(
            entity_type=_ENTITY_TYPE
        )
    )


def upgrade() -> None:
    op.create_table(
        "vfolder_auto_mounts",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=False),
        sa.Column("vfolder_id", sa.Uuid(), nullable=False),
        sa.Column("mount_destination", sa.Text(), nullable=False),
        sa.Column("subpath", sa.Text(), nullable=False, server_default="."),
        sa.Column("mount_permission", sa.VARCHAR(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vfolder_auto_mounts")),
        sa.ForeignKeyConstraint(
            ["scope_type", "scope_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            name=op.f("fk_vfolder_auto_mounts_scope_type_virtual_entities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vfolder_id"],
            ["vfolders.id"],
            name=op.f("fk_vfolder_auto_mounts_vfolder_id_vfolders"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "uq_vfolder_auto_mounts_live_vfolder",
        "vfolder_auto_mounts",
        ["scope_type", "scope_id", "vfolder_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_vfolder_auto_mounts_live_destination",
        "vfolder_auto_mounts",
        ["scope_type", "scope_id", "mount_destination"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    _grant(op.get_bind())


def downgrade() -> None:
    _revoke(op.get_bind())
    op.drop_index("uq_vfolder_auto_mounts_live_destination", table_name="vfolder_auto_mounts")
    op.drop_index("uq_vfolder_auto_mounts_live_vfolder", table_name="vfolder_auto_mounts")
    op.drop_table("vfolder_auto_mounts")
