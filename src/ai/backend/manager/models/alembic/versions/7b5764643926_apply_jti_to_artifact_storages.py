"""Apply joined table inheritance to artifact_storages

Revision ID: 7b5764643926
Revises: 35dfab3b0662
Create Date: 2026-02-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "7b5764643926"
down_revision = "35dfab3b0662"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. For each row in artifact_storages, set id = storage_id (align PKs)
    #    We need to update artifact_storages.id to match the child table id (storage_id).
    #    Since id is a PK, we need to handle this carefully.
    conn.execute(
        sa.text("""
        UPDATE artifact_storages SET id = storage_id
    """)
    )

    # 2. Drop the storage_id unique constraint and column
    op.drop_constraint("uq_artifact_storages_storage_id", "artifact_storages", type_="unique")
    op.drop_column("artifact_storages", "storage_id")

    # 3. Add FK constraints: child.id -> artifact_storages.id
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

    # 1. Drop FK constraints
    op.drop_constraint("fk_vfs_storages_id_artifact_storages", "vfs_storages", type_="foreignkey")
    op.drop_constraint(
        "fk_object_storages_id_artifact_storages", "object_storages", type_="foreignkey"
    )

    # 2. Re-add storage_id column (copy id into it, since they were aligned)
    op.add_column(
        "artifact_storages",
        sa.Column("storage_id", GUID(), nullable=True),
    )

    conn.execute(
        sa.text("""
        UPDATE artifact_storages SET storage_id = id
    """)
    )

    op.alter_column("artifact_storages", "storage_id", nullable=False)

    op.create_unique_constraint(
        "uq_artifact_storages_storage_id", "artifact_storages", ["storage_id"]
    )
