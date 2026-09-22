from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("StorageNamespaceRow",)


class StorageNamespaceRow(Base):
    __tablename__ = "storage_namespace"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("storage_id", "namespace", name="uq_storage_id_namespace"),
    )

    id: Mapped[StorageNamespaceID] = mapped_column(
        "id",
        GUID(StorageNamespaceID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    storage_id: Mapped[ObjectStorageID] = mapped_column(
        "storage_id",
        GUID(ObjectStorageID),
        nullable=False,
    )
    namespace: Mapped[str] = mapped_column("namespace", sa.String, nullable=False)
