"""add the storage volume and backend schema

Revision ID: c7d2fb1e5a90
Revises: d5b3f8c26a41
Create Date: 2026-09-04

"""

from typing import Any

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "c7d2fb1e5a90"
down_revision = "d5b3f8c26a41"
branch_labels = None
depends_on = None


# name, supports_vfolder, supports_metric, supports_quota,
# supports_fast_fs_size, supports_fast_scan, supports_fast_size
_BUILTIN_BACKEND_TYPES: list[tuple[str, bool, bool, bool, bool, bool, bool]] = [
    ("vfs", True, False, False, False, False, False),
    ("xfs", True, False, True, False, False, False),
    ("cephfs", True, False, True, False, False, True),
    ("purestorage", True, True, False, True, True, False),
    ("netapp", True, True, True, True, False, True),
    ("weka", True, True, True, True, False, False),
    ("gpfs", True, True, True, True, False, False),
    ("spectrumscale", True, True, True, True, False, False),
    ("dellemc-onefs", True, True, True, True, False, False),
    ("vast", True, True, True, True, False, True),
    ("exascaler", True, False, True, False, False, False),
    ("hammerspace", True, False, True, False, False, False),
    ("hammerspace-base", True, False, False, False, False, False),
    ("noop", False, False, False, False, False, False),
]


def _timestamp_columns() -> list[sa.Column[Any]]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "storage_backends",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("supports_vfolder", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("supports_metric", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("supports_quota", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("supports_fast_fs_size", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("supports_fast_scan", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("supports_fast_size", sa.Boolean(), server_default=sa.false(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_backends")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_backends_name")),
    )

    op.create_table(
        "service_storage_backends",
        sa.Column("service_catalog_id", GUID(), nullable=False),
        sa.Column("storage_backend_id", GUID(), nullable=False),
        sa.Column(
            "status", sa.String(length=64), server_default=sa.text("'healthy'"), nullable=False
        ),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "service_catalog_id",
            "storage_backend_id",
            name=op.f("pk_service_storage_backends"),
        ),
        sa.ForeignKeyConstraint(
            ["service_catalog_id"],
            ["service_catalog.id"],
            name=op.f("fk_service_storage_backends_service_catalog_id_service_catalog"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_backend_id"],
            ["storage_backends.id"],
            name="fk_service_storage_backends_storage_backend_id",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "storage_volumes",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("storage_backend_id", GUID(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_volumes")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_volumes_name")),
        sa.ForeignKeyConstraint(
            ["storage_backend_id"],
            ["storage_backends.id"],
            name=op.f("fk_storage_volumes_storage_backend_id_storage_backends"),
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "uq_storage_volumes_is_default",
        "storage_volumes",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )

    op.create_table(
        "service_storage_volumes",
        sa.Column("service_catalog_id", GUID(), nullable=False),
        sa.Column("storage_volume_id", GUID(), nullable=False),
        sa.Column("mount_path", sa.String(), nullable=False),
        sa.Column(
            "status", sa.String(length=64), server_default=sa.text("'healthy'"), nullable=False
        ),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "service_catalog_id",
            "storage_volume_id",
            name=op.f("pk_service_storage_volumes"),
        ),
        sa.ForeignKeyConstraint(
            ["service_catalog_id"],
            ["service_catalog.id"],
            name=op.f("fk_service_storage_volumes_service_catalog_id_service_catalog"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_volume_id"],
            ["storage_volumes.id"],
            name=op.f("fk_service_storage_volumes_storage_volume_id_storage_volumes"),
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "resource_group_storage_volumes",
        sa.Column("resource_group_id", GUID(), nullable=False),
        sa.Column("storage_volume_id", GUID(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "resource_group_id",
            "storage_volume_id",
            name=op.f("pk_resource_group_storage_volumes"),
        ),
        sa.ForeignKeyConstraint(
            ["resource_group_id"],
            ["scaling_groups.id"],
            name="fk_rg_storage_volumes_resource_group_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_volume_id"],
            ["storage_volumes.id"],
            name="fk_rg_storage_volumes_storage_volume_id",
            ondelete="CASCADE",
        ),
    )

    op.add_column("vfolders", sa.Column("storage_volume_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_vfolders_storage_volume_id_storage_volumes"),
        "vfolders",
        "storage_volumes",
        ["storage_volume_id"],
        ["id"],
        ondelete="SET NULL",
    )

    storage_backends = sa.table(
        "storage_backends",
        sa.column("name", sa.String),
        sa.column("type", sa.String),
        sa.column("supports_vfolder", sa.Boolean),
        sa.column("supports_metric", sa.Boolean),
        sa.column("supports_quota", sa.Boolean),
        sa.column("supports_fast_fs_size", sa.Boolean),
        sa.column("supports_fast_scan", sa.Boolean),
        sa.column("supports_fast_size", sa.Boolean),
    )
    op.bulk_insert(
        storage_backends,
        [
            {
                "name": name,
                "type": name,
                "supports_vfolder": vfolder,
                "supports_metric": metric,
                "supports_quota": quota,
                "supports_fast_fs_size": fast_fs_size,
                "supports_fast_scan": fast_scan,
                "supports_fast_size": fast_size,
            }
            for (
                name,
                vfolder,
                metric,
                quota,
                fast_fs_size,
                fast_scan,
                fast_size,
            ) in _BUILTIN_BACKEND_TYPES
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_vfolders_storage_volume_id_storage_volumes"), "vfolders", type_="foreignkey"
    )
    op.drop_column("vfolders", "storage_volume_id")
    op.drop_table("resource_group_storage_volumes")
    op.drop_table("service_storage_volumes")
    op.drop_table("storage_volumes")
    op.drop_table("service_storage_backends")
    op.drop_table("storage_backends")
