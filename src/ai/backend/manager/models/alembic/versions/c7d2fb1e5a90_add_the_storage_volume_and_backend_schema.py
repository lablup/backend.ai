"""add the storage volume and backend schema

Revision ID: c7d2fb1e5a90
Revises: c7a4f1e9b023
Create Date: 2026-09-04

"""

from typing import Any

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "c7d2fb1e5a90"
down_revision = "c7a4f1e9b023"
branch_labels = None
depends_on = None


# Capability names a volume implementation reports.
_BUILTIN_BACKEND_TYPES: list[tuple[str, list[str]]] = [
    ("vfs", ["vfolder"]),
    ("xfs", ["vfolder", "quota"]),
    ("cephfs", ["vfolder", "quota", "fast-size"]),
    ("purestorage", ["vfolder", "metric", "fast-fs-size", "fast-scan"]),
    ("netapp", ["vfolder", "metric", "quota", "fast-fs-size", "fast-size"]),
    ("weka", ["vfolder", "metric", "quota", "fast-fs-size"]),
    ("gpfs", ["vfolder", "metric", "quota", "fast-fs-size"]),
    ("spectrumscale", ["vfolder", "metric", "quota", "fast-fs-size"]),
    ("dellemc-onefs", ["vfolder", "metric", "quota", "fast-fs-size"]),
    ("vast", ["vfolder", "metric", "quota", "fast-fs-size", "fast-size"]),
    ("exascaler", ["vfolder", "quota"]),
    ("hammerspace", ["vfolder", "quota"]),
    ("hammerspace-base", ["vfolder"]),
    ("noop", []),
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
        "storage_backend_types",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column(
            "capabilities",
            sa.ARRAY(sa.String(length=64)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_backend_types")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_backend_types_name")),
    )

    op.create_table(
        "storage_backends",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type_id", GUID(), nullable=False),
        sa.Column(
            "status_stale_after",
            sa.Interval(),
            server_default=sa.text("'3600 seconds'"),
            nullable=False,
        ),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_backends")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_backends_name")),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["storage_backend_types.id"],
            name="fk_storage_backends_type_id",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "service_storage_backends",
        sa.Column("service_catalog_id", GUID(), nullable=False),
        sa.Column("storage_backend_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("status_checked_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.Column(
            "status_stale_after",
            sa.Interval(),
            server_default=sa.text("'3600 seconds'"),
            nullable=False,
        ),
        sa.Column("expose_percentage", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("expose_used_bytes", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("expose_capacity_bytes", sa.Boolean(), server_default=sa.false(), nullable=False),
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
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("status_checked_at", sa.DateTime(timezone=True), nullable=False),
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

    storage_backend_types = sa.table(
        "storage_backend_types",
        sa.column("name", sa.String),
        sa.column("capabilities", sa.ARRAY(sa.String)),
    )
    op.bulk_insert(
        storage_backend_types,
        [
            {"name": name, "capabilities": capabilities}
            for name, capabilities in _BUILTIN_BACKEND_TYPES
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
    op.drop_table("storage_backend_types")
