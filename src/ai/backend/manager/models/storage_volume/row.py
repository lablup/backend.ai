from __future__ import annotations

from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import (
    DEFAULT_STATUS_STALE_AFTER,
    ServiceStorageStatus,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = (
    "ResourceGroupVolumeOfferRow",
    "StorageVolumeRow",
    "StorageVolumeServiceHoldingRow",
)


class StorageVolumeRow(LifecycleTimestampsMixin, Base):
    """A volume on a storage backend, identified by the name every service declares it under.

    Carries no status: a volume no service reports is unreachable rather than unhealthy.
    Mounts are the holding service's own concern and are not recorded here.
    """

    __tablename__ = "storage_volumes"

    id: Mapped[StorageVolumeID] = mapped_column(
        "id",
        GUID(StorageVolumeID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), nullable=False)
    storage_backend_id: Mapped[StorageBackendID] = mapped_column(
        "storage_backend_id",
        GUID(StorageBackendID),
        sa.ForeignKey("storage_backends.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # How long this may go without a fresh check before its status counts as stale.
    status_stale_after: Mapped[timedelta] = mapped_column(
        "status_stale_after",
        sa.Interval,
        nullable=False,
        server_default=sa.text(f"'{int(DEFAULT_STATUS_STALE_AFTER.total_seconds())} seconds'"),
    )
    # Which usage figures this volume reports to a user. A percentage tells how full the
    # volume is without disclosing its size, which is why it alone is exposed by default.
    expose_percentage: Mapped[bool] = mapped_column(
        "expose_percentage", sa.Boolean, nullable=False, server_default=sa.true()
    )
    expose_used_bytes: Mapped[bool] = mapped_column(
        "expose_used_bytes", sa.Boolean, nullable=False, server_default=sa.false()
    )
    expose_capacity_bytes: Mapped[bool] = mapped_column(
        "expose_capacity_bytes", sa.Boolean, nullable=False, server_default=sa.false()
    )


class StorageVolumeServiceHoldingRow(LifecycleTimestampsMixin, Base):
    """A storage volume as one service holds it.

    The status is what the service's volume implementation derives from its mounts.
    """

    __tablename__ = "storage_volume_service_holdings"

    service_catalog_id: Mapped[ServiceCatalogID] = mapped_column(
        "service_catalog_id",
        GUID(ServiceCatalogID),
        sa.ForeignKey(
            "service_catalog.id",
            ondelete="CASCADE",
            name="fk_storage_volume_service_holdings_service_catalog_id",
        ),
        primary_key=True,
    )
    storage_volume_id: Mapped[StorageVolumeID] = mapped_column(
        "storage_volume_id",
        GUID(StorageVolumeID),
        sa.ForeignKey(
            "storage_volumes.id",
            ondelete="RESTRICT",
            name="fk_storage_volume_service_holdings_storage_volume_id",
        ),
        primary_key=True,
    )
    status: Mapped[ServiceStorageStatus] = mapped_column(
        "status", StrEnumType(ServiceStorageStatus), nullable=False
    )
    # When the service measured ``status``, not when its heartbeat delivered it.
    status_checked_at: Mapped[datetime] = mapped_column(
        "status_checked_at", sa.DateTime(timezone=True), nullable=False
    )


class ResourceGroupVolumeOfferRow(LifecycleTimestampsMixin, Base):
    """A storage volume offered to a resource group."""

    __tablename__ = "resource_group_volume_offers"

    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        sa.ForeignKey(
            "scaling_groups.id",
            ondelete="CASCADE",
            name="fk_resource_group_volume_offers_resource_group_id",
        ),
        primary_key=True,
    )
    storage_volume_id: Mapped[StorageVolumeID] = mapped_column(
        "storage_volume_id",
        GUID(StorageVolumeID),
        sa.ForeignKey(
            "storage_volumes.id",
            ondelete="CASCADE",
            name="fk_resource_group_volume_offers_storage_volume_id",
        ),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.true()
    )
    # At most one volume may be the default within a resource group.
    is_default: Mapped[bool] = mapped_column(
        "is_default", sa.Boolean, nullable=False, server_default=sa.false()
    )

    __table_args__ = (
        sa.Index(
            "uq_resource_group_volume_offers_is_default",
            "resource_group_id",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
    )
