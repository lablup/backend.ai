from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_backend_type import StorageBackendTypeID
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = (
    "ServiceStorageBackendStatusRow",
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
    capabilities: Mapped[StorageBackendCapabilities] = mapped_column(
        "capabilities",
        PydanticColumn(StorageBackendCapabilities),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )


class StorageBackendRow(LifecycleTimestampsMixin, Base):
    """A storage appliance a service can reach.

    Carries no status: only the services that hold its volumes can reach it, each over
    its own network path, so the observation lives on `service_storage_backend_status`. How the
    appliance is reached is the service's own configuration and is not stored here.
    """

    __tablename__ = "storage_backends"

    id: Mapped[StorageBackendID] = mapped_column(
        "id",
        GUID(StorageBackendID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), nullable=False)
    storage_backend_type_id: Mapped[StorageBackendTypeID] = mapped_column(
        "storage_backend_type_id",
        GUID(StorageBackendTypeID),
        sa.ForeignKey(
            "storage_backend_types.id",
            ondelete="RESTRICT",
            name="fk_storage_backends_storage_backend_type_id",
        ),
        nullable=False,
    )


class ServiceStorageBackendStatusRow(LifecycleTimestampsMixin, Base):
    """A storage backend as one service sees it."""

    __tablename__ = "service_storage_backend_status"

    service_catalog_id: Mapped[ServiceCatalogID] = mapped_column(
        "service_catalog_id",
        GUID(ServiceCatalogID),
        sa.ForeignKey(
            "service_catalog.id",
            ondelete="CASCADE",
            name="fk_service_storage_backend_status_service_catalog_id",
        ),
        primary_key=True,
    )
    storage_backend_id: Mapped[StorageBackendID] = mapped_column(
        "storage_backend_id",
        GUID(StorageBackendID),
        sa.ForeignKey(
            "storage_backends.id",
            ondelete="RESTRICT",
            name="fk_service_storage_backend_status_storage_backend_id",
        ),
        primary_key=True,
    )
    status_checked_at: Mapped[datetime | None] = mapped_column(
        "status_checked_at", sa.DateTime(timezone=True), nullable=True
    )
