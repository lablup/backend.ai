from __future__ import annotations

from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_backend_type import StorageBackendTypeID
from ai.backend.common.data.storage.types import (
    DEFAULT_STATUS_STALE_AFTER,
    ServiceStorageStatus,
    StorageBackendType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = (
    "ServiceStorageBackendRow",
    "StorageBackendRow",
    "StorageBackendTypeRow",
)


class StorageBackendTypeRow(LifecycleTimestampsMixin, Base):
    """A storage backend implementation a volume can be served by.

    The capabilities come from the implementation, not from any one appliance, so they
    live here. Built-in types are seeded; a storage backend plugin adds its own.
    """

    __tablename__ = "storage_backend_types"

    id: Mapped[StorageBackendTypeID] = mapped_column(
        "id",
        GUID(StorageBackendTypeID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[StorageBackendType] = mapped_column(
        "name", sa.String(length=64), unique=True, nullable=False
    )
    supports_vfolder: Mapped[bool] = mapped_column(
        "supports_vfolder", sa.Boolean, nullable=False, server_default=sa.false()
    )
    supports_metric: Mapped[bool] = mapped_column(
        "supports_metric", sa.Boolean, nullable=False, server_default=sa.false()
    )
    supports_quota: Mapped[bool] = mapped_column(
        "supports_quota", sa.Boolean, nullable=False, server_default=sa.false()
    )
    supports_fast_fs_size: Mapped[bool] = mapped_column(
        "supports_fast_fs_size", sa.Boolean, nullable=False, server_default=sa.false()
    )
    supports_fast_scan: Mapped[bool] = mapped_column(
        "supports_fast_scan", sa.Boolean, nullable=False, server_default=sa.false()
    )
    supports_fast_size: Mapped[bool] = mapped_column(
        "supports_fast_size", sa.Boolean, nullable=False, server_default=sa.false()
    )


class StorageBackendRow(LifecycleTimestampsMixin, Base):
    """A storage appliance a service can reach.

    Carries no status: only the services that mount its volumes can reach it, each over
    its own network path, so the observation lives on `service_storage_backends`. How the
    appliance is reached is the service's own configuration and is not stored here.
    """

    __tablename__ = "storage_backends"

    id: Mapped[StorageBackendID] = mapped_column(
        "id",
        GUID(StorageBackendID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), unique=True, nullable=False)
    type_id: Mapped[StorageBackendTypeID] = mapped_column(
        "type_id",
        GUID(StorageBackendTypeID),
        sa.ForeignKey("storage_backend_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # How long this may go without a fresh check before its status counts as stale.
    status_stale_after: Mapped[timedelta] = mapped_column(
        "status_stale_after",
        sa.Interval,
        nullable=False,
        server_default=sa.text(f"'{int(DEFAULT_STATUS_STALE_AFTER.total_seconds())} seconds'"),
    )


class ServiceStorageBackendRow(LifecycleTimestampsMixin, Base):
    """A storage backend as one service reports it."""

    __tablename__ = "service_storage_backends"

    service_catalog_id: Mapped[ServiceCatalogID] = mapped_column(
        "service_catalog_id",
        GUID(ServiceCatalogID),
        sa.ForeignKey("service_catalog.id", ondelete="CASCADE"),
        primary_key=True,
    )
    storage_backend_id: Mapped[StorageBackendID] = mapped_column(
        "storage_backend_id",
        GUID(StorageBackendID),
        sa.ForeignKey(
            "storage_backends.id",
            ondelete="RESTRICT",
            name="fk_service_storage_backends_storage_backend_id",
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
