from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.storage.types import (
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
    type: Mapped[StorageBackendType] = mapped_column(
        "type", StrEnumType(StorageBackendType), nullable=False
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
        "status",
        StrEnumType(ServiceStorageStatus),
        nullable=False,
        server_default=ServiceStorageStatus.HEALTHY.value,
    )
