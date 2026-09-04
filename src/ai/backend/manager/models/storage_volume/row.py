from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import ServiceStorageStatus
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = (
    "ResourceGroupStorageVolumeRow",
    "ServiceStorageVolumeRow",
    "StorageVolumeRow",
)


class StorageVolumeRow(LifecycleTimestampsMixin, Base):
    """A volume on a storage backend, identified by the name every service declares it under.

    Carries neither a path nor a status: the path differs per service, and a volume no
    service reports is unreachable rather than unhealthy.
    """

    __tablename__ = "storage_volumes"
    __table_args__ = (
        # Partial unique index: at most one row may have is_default = true.
        sa.Index(
            "uq_storage_volumes_is_default",
            "is_default",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
    )

    id: Mapped[StorageVolumeID] = mapped_column(
        "id",
        GUID(StorageVolumeID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), unique=True, nullable=False)
    storage_backend_id: Mapped[StorageBackendID] = mapped_column(
        "storage_backend_id",
        GUID(StorageBackendID),
        sa.ForeignKey("storage_backends.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # At most one volume may be the default at a time, enforced by the partial unique
    # index in ``__table_args__`` (a minimum of one is NOT guaranteed). To switch the
    # default, clear the previous one before setting the new one in the same transaction.
    is_default: Mapped[bool] = mapped_column(
        "is_default", sa.Boolean, nullable=False, server_default=sa.false()
    )


class ServiceStorageVolumeRow(LifecycleTimestampsMixin, Base):
    """A storage volume as one service mounts it."""

    __tablename__ = "service_storage_volumes"

    service_catalog_id: Mapped[ServiceCatalogID] = mapped_column(
        "service_catalog_id",
        GUID(ServiceCatalogID),
        sa.ForeignKey("service_catalog.id", ondelete="CASCADE"),
        primary_key=True,
    )
    storage_volume_id: Mapped[StorageVolumeID] = mapped_column(
        "storage_volume_id",
        GUID(StorageVolumeID),
        sa.ForeignKey("storage_volumes.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    mount_path: Mapped[str] = mapped_column("mount_path", sa.String, nullable=False)
    status: Mapped[ServiceStorageStatus] = mapped_column(
        "status",
        StrEnumType(ServiceStorageStatus),
        nullable=False,
        server_default=ServiceStorageStatus.HEALTHY.value,
    )


class ResourceGroupStorageVolumeRow(LifecycleTimestampsMixin, Base):
    """A storage volume offered to a resource group."""

    __tablename__ = "resource_group_storage_volumes"

    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        sa.ForeignKey(
            "scaling_groups.id",
            ondelete="CASCADE",
            name="fk_rg_storage_volumes_resource_group_id",
        ),
        primary_key=True,
    )
    storage_volume_id: Mapped[StorageVolumeID] = mapped_column(
        "storage_volume_id",
        GUID(StorageVolumeID),
        sa.ForeignKey(
            "storage_volumes.id",
            ondelete="CASCADE",
            name="fk_rg_storage_volumes_storage_volume_id",
        ),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.true()
    )
