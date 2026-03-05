"""Add artifact_storages common table with JTI

Revision ID: 35dfab3b0662
Revises: 3f5c20f7bb07
Create Date: 2025-12-02 09:24:21.050932

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "35dfab3b0662"
down_revision = "3f5c20f7bb07"
branch_labels = None
depends_on = None


def _migrate_object_storages_to_artifact_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate existing object_storages records to artifact_storages (JTI: id = child id)."""
    conn.execute(
        sa.text("""
        INSERT INTO artifact_storages (id, name, type)
        SELECT id, name, 'object_storage'
        FROM object_storages
        WHERE name IS NOT NULL
    """)
    )

    # Drop the name column and constraint
    op.drop_index("ix_object_storages_name", table_name="object_storages")
    op.drop_column("object_storages", "name")


def _migrate_vfs_storages_to_artifact_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate existing vfs_storages records to artifact_storages (JTI: id = child id)."""
    conn.execute(
        sa.text("""
        INSERT INTO artifact_storages (id, name, type)
        SELECT id, name, 'vfs_storage'
        FROM vfs_storages
        WHERE name IS NOT NULL
    """)
    )

    # Drop the name column and constraint
    op.drop_index("ix_vfs_storages_name", table_name="vfs_storages")
    op.drop_column("vfs_storages", "name")


def _migrate_artifact_storages_to_object_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate data back from artifact_storages to object_storages."""
    conn.execute(
        sa.text("""
        UPDATE object_storages o
        SET name = a.name
        FROM artifact_storages a
        WHERE o.id = a.id AND a.type = 'object_storage'
    """)
    )


def _migrate_artifact_storages_to_vfs_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate data back from artifact_storages to vfs_storages."""
    conn.execute(
        sa.text("""
        UPDATE vfs_storages v
        SET name = a.name
        FROM artifact_storages a
        WHERE v.id = a.id AND a.type = 'vfs_storage'
    """)
    )


def upgrade() -> None:
    op.create_table(
        "artifact_storages",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_artifact_storages")),
        sa.UniqueConstraint("name", name=op.f("uq_artifact_storages_name")),
    )

    conn = op.get_bind()

    _migrate_object_storages_to_artifact_storages(conn)
    _migrate_vfs_storages_to_artifact_storages(conn)

    # Add FK constraints: child.id → artifact_storages.id (JTI)
    op.create_foreign_key(
        "fk_object_storages_id_artifact_storages",
        "object_storages",
        "artifact_storages",
        ["id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_vfs_storages_id_artifact_storages",
        "vfs_storages",
        "artifact_storages",
        ["id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop FK constraints
    op.drop_constraint(
        "fk_object_storages_id_artifact_storages", "object_storages", type_="foreignkey"
    )
    op.drop_constraint("fk_vfs_storages_id_artifact_storages", "vfs_storages", type_="foreignkey")

    # Add name column back to object_storages
    op.add_column(
        "object_storages",
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    _migrate_artifact_storages_to_object_storages(conn)

    # Make name column NOT NULL
    op.alter_column(
        "object_storages",
        "name",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    # Recreate constraints
    op.create_index("ix_object_storages_name", "object_storages", ["name"], unique=True)

    # Add name column back to vfs_storages
    op.add_column(
        "vfs_storages",
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    _migrate_artifact_storages_to_vfs_storages(conn)

    # Make name column NOT NULL
    op.alter_column(
        "vfs_storages",
        "name",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    # Recreate constraints
    op.create_index("ix_vfs_storages_name", "vfs_storages", ["name"], unique=True)

    op.drop_table("artifact_storages")
