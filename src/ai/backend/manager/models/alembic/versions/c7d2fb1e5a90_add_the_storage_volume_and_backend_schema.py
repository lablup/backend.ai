"""add the storage volume and backend schema

Revision ID: c7d2fb1e5a90
Revises: d17b4e9c25a8
Create Date: 2026-09-04

"""

import uuid
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "c7d2fb1e5a90"
down_revision = "d17b4e9c25a8"
branch_labels = None
depends_on = None


# Ids and capability names as fixtures/manager/example-storage-backend-types.json carries
# them, so a migrated database and a fixture-populated one hold the same rows.
_BUILTIN_BACKEND_TYPES: list[tuple[str, str, list[str]]] = [
    ("01a0f746-b6d3-72d2-9e9a-a544b9652bcd", "vfs", ["vfolder"]),
    ("01a0f746-b6d4-7fdd-a23e-c95ecaad2c62", "xfs", ["vfolder", "quota"]),
    ("01a0f746-b6d5-7895-a119-c45f92d8d89a", "cephfs", ["vfolder", "quota", "fast-size"]),
    (
        "01a0f746-b6d6-747e-a8ee-870a4213b94a",
        "purestorage",
        ["vfolder", "metric", "fast-fs-size", "fast-scan"],
    ),
    (
        "01a0f746-b6d7-7b8c-946a-f478acd05689",
        "netapp",
        ["vfolder", "metric", "quota", "fast-fs-size", "fast-size"],
    ),
    (
        "01a0f746-b6d8-7cda-9ead-032dc99d3611",
        "weka",
        ["vfolder", "metric", "quota", "fast-fs-size"],
    ),
    (
        "01a0f746-b6d9-775d-ba54-e6b4ba0b86f4",
        "gpfs",
        ["vfolder", "metric", "quota", "fast-fs-size"],
    ),
    (
        "01a0f746-b6da-7e3c-8633-ceaffa04892e",
        "spectrumscale",
        ["vfolder", "metric", "quota", "fast-fs-size"],
    ),
    (
        "01a0f746-b6db-7bc1-925b-9a4603421848",
        "dellemc-onefs",
        ["vfolder", "metric", "quota", "fast-fs-size"],
    ),
    (
        "01a0f746-b6dc-7409-bec6-12b74452d7de",
        "vast",
        ["vfolder", "metric", "quota", "fast-fs-size", "fast-size"],
    ),
    ("01a0f746-b6dd-7113-bfd8-8c37075724f2", "exascaler", ["vfolder", "quota"]),
    ("01a0f746-b6de-7cac-92dd-c23348356510", "hammerspace", ["vfolder", "quota"]),
    ("01a0f746-b6df-7b9b-be97-35f559617a35", "hammerspace-base", ["vfolder"]),
    ("01a0f746-b6e0-7efc-8855-34cab4efcea3", "noop", []),
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
            pgsql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
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
        sa.Column("storage_backend_type_id", GUID(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_backends")),
        sa.ForeignKeyConstraint(
            ["storage_backend_type_id"],
            ["storage_backend_types.id"],
            name="fk_storage_backends_storage_backend_type_id",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "service_storage_backend_status",
        sa.Column("service_catalog_id", GUID(), nullable=False),
        sa.Column("storage_backend_id", GUID(), nullable=False),
        sa.Column("status_checked_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "service_catalog_id",
            "storage_backend_id",
            name=op.f("pk_service_storage_backend_status"),
        ),
        sa.ForeignKeyConstraint(
            ["service_catalog_id"],
            ["service_catalog.id"],
            name="fk_service_storage_backend_status_service_catalog_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_backend_id"],
            ["storage_backends.id"],
            name="fk_service_storage_backend_status_storage_backend_id",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "storage_volumes",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("storage_backend_id", GUID(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["storage_backend_id"],
            ["storage_backends.id"],
            name=op.f("fk_storage_volumes_storage_backend_id_storage_backends"),
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "storage_volume_service_holdings",
        sa.Column("service_catalog_id", GUID(), nullable=False),
        sa.Column("storage_volume_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("status_checked_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "service_catalog_id",
            "storage_volume_id",
            name=op.f("pk_storage_volume_service_holdings"),
        ),
        sa.ForeignKeyConstraint(
            ["service_catalog_id"],
            ["service_catalog.id"],
            name="fk_storage_volume_service_holdings_service_catalog_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_volume_id"],
            ["storage_volumes.id"],
            name="fk_storage_volume_service_holdings_storage_volume_id",
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "resource_group_volume_offers",
        sa.Column("resource_group_id", GUID(), nullable=False),
        sa.Column("storage_volume_id", GUID(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        *_timestamp_columns(),
        sa.PrimaryKeyConstraint(
            "resource_group_id",
            "storage_volume_id",
            name=op.f("pk_resource_group_volume_offers"),
        ),
        sa.ForeignKeyConstraint(
            ["resource_group_id"],
            ["scaling_groups.id"],
            name="fk_resource_group_volume_offers_resource_group_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["storage_volume_id"],
            ["storage_volumes.id"],
            name="fk_resource_group_volume_offers_storage_volume_id",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "uq_resource_group_volume_offers_is_default",
        "resource_group_volume_offers",
        ["resource_group_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
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
        sa.column("id", GUID),
        sa.column("name", sa.String),
        sa.column("capabilities", pgsql.JSONB),
    )
    op.bulk_insert(
        storage_backend_types,
        [
            {"id": uuid.UUID(id_), "name": name, "capabilities": {"supported": capabilities}}
            for id_, name, capabilities in _BUILTIN_BACKEND_TYPES
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_vfolders_storage_volume_id_storage_volumes"), "vfolders", type_="foreignkey"
    )
    op.drop_column("vfolders", "storage_volume_id")
    op.drop_table("resource_group_volume_offers")
    op.drop_table("storage_volume_service_holdings")
    op.drop_table("storage_volumes")
    op.drop_table("service_storage_backend_status")
    op.drop_table("storage_backends")
    op.drop_table("storage_backend_types")
