"""Service Catalog Row models.

Database models for the unified service catalog:
- ServiceCatalogRow: Registered service instances with health status
- ServiceCatalogEndpointRow: Endpoints exposed by each service instance
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

__all__ = (
    "ServiceCatalogRow",
    "ServiceCatalogEndpointRow",
)


class ServiceCatalogRow(Base):  # type: ignore[misc]
    """A registered service instance in the service catalog.

    Tracks service identity, health status, and heartbeat information.
    """

    __tablename__ = "service_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    service_group: Mapped[str] = mapped_column(
        "service_group", sa.String(length=64), nullable=False
    )
    instance_id: Mapped[str] = mapped_column("instance_id", sa.String(length=128), nullable=False)
    display_name: Mapped[str] = mapped_column("display_name", sa.String(length=256), nullable=False)
    version: Mapped[str] = mapped_column("version", sa.String(length=64), nullable=False)
    labels: Mapped[dict[str, Any]] = mapped_column(
        "labels", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    status: Mapped[ServiceCatalogStatus] = mapped_column(
        "status", StrEnumType(ServiceCatalogStatus), nullable=False
    )
    startup_time: Mapped[datetime] = mapped_column(
        "startup_time", sa.DateTime(timezone=True), nullable=False
    )
    registered_at: Mapped[datetime] = mapped_column(
        "registered_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    last_heartbeat: Mapped[datetime] = mapped_column(
        "last_heartbeat",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    config_hash: Mapped[str] = mapped_column(
        "config_hash", sa.String(length=128), nullable=False, server_default=sa.text("''")
    )

    endpoints: Mapped[list[ServiceCatalogEndpointRow]] = relationship(
        "ServiceCatalogEndpointRow",
        back_populates="service",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "service_group",
            "instance_id",
            name="uq_service_catalog_service_group_instance_id",
        ),
        sa.Index("ix_service_catalog_service_group", "service_group"),
        sa.Index("ix_service_catalog_status", "status"),
    )


class ServiceCatalogEndpointRow(Base):  # type: ignore[misc]
    """An endpoint exposed by a service instance.

    Describes how a specific role/scope of a service can be reached.
    """

    __tablename__ = "service_catalog_endpoint"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        "service_id",
        GUID,
        sa.ForeignKey("service_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column("role", sa.String(length=32), nullable=False)
    scope: Mapped[str] = mapped_column("scope", sa.String(length=32), nullable=False)
    address: Mapped[str] = mapped_column("address", sa.String(length=256), nullable=False)
    port: Mapped[int] = mapped_column("port", sa.Integer, nullable=False)
    protocol: Mapped[str] = mapped_column("protocol", sa.String(length=16), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")
    )

    service: Mapped[ServiceCatalogRow] = relationship(
        "ServiceCatalogRow",
        back_populates="endpoints",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "service_id",
            "role",
            "scope",
            name="uq_service_catalog_endpoint_service_id_role_scope",
        ),
    )
