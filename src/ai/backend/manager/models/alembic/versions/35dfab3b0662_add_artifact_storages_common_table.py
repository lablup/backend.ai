"""Add artifact_storages common table

Revision ID: 35dfab3b0662
Revises: ccf8ae5c90fe
Create Date: 2025-12-02 09:24:21.050932

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "35dfab3b0662"
down_revision = "ccf8ae5c90fe"
branch_labels = None
depends_on = None


def _migrate_object_storages_to_artifact_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate existing object_storages records to artifact_storages."""
    result = conn.execute(
        sa.text("""
        SELECT id, name FROM object_storages
        WHERE name IS NOT NULL
    """)
    )

    for row in result:
        conn.execute(
            sa.text("""
            INSERT INTO artifact_storages (name, storage_id, type)
            VALUES (:name, :storage_id, :type)
        """),
            {"name": row.name, "storage_id": row.id, "type": "object_storage"},
        )

    # Drop the name column and constraint
    op.drop_index("ix_object_storages_name", table_name="object_storages")
    op.drop_column("object_storages", "name")


def _migrate_vfs_storages_to_artifact_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate existing vfs_storages records to artifact_storages."""
    result = conn.execute(
        sa.text("""
        SELECT id, name FROM vfs_storages
        WHERE name IS NOT NULL
    """)
    )

    for row in result:
        conn.execute(
            sa.text("""
            INSERT INTO artifact_storages (name, storage_id, type)
            VALUES (:name, :storage_id, :type)
        """),
            {"name": row.name, "storage_id": row.id, "type": "vfs_storage"},
        )

    # Drop the name column and constraint
    op.drop_index("ix_vfs_storages_name", table_name="vfs_storages")
    op.drop_column("vfs_storages", "name")


def _migrate_artifact_storages_to_object_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate data back from artifact_storages to object_storages."""
    result = conn.execute(
        sa.text("""
        SELECT name, storage_id FROM artifact_storages
        WHERE type = 'object_storage'
    """)
    )

    for row in result:
        conn.execute(
            sa.text("""
            UPDATE object_storages
            SET name = :name
            WHERE id = :storage_id
        """),
            {"name": row.name, "storage_id": row.storage_id},
        )


def _migrate_artifact_storages_to_vfs_storages(
    conn: sa.engine.Connection,
) -> None:
    """Migrate data back from artifact_storages to vfs_storages."""
    result = conn.execute(
        sa.text("""
        SELECT name, storage_id FROM artifact_storages
        WHERE type = 'vfs_storage'
    """)
    )

    for row in result:
        conn.execute(
            sa.text("""
            UPDATE vfs_storages
            SET name = :name
            WHERE id = :storage_id
        """),
            {"name": row.name, "storage_id": row.storage_id},
        )


def upgrade() -> None:
    op.create_table(
        "artifact_storages",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("storage_id", GUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_artifact_storages")),
        sa.UniqueConstraint("name", name=op.f("uq_artifact_storages_name")),
        sa.UniqueConstraint("storage_id", name=op.f("uq_artifact_storages_storage_id")),
    )

    conn = op.get_bind()

    _migrate_object_storages_to_artifact_storages(conn)
    _migrate_vfs_storages_to_artifact_storages(conn)


def downgrade() -> None:
    conn = op.get_bind()

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
