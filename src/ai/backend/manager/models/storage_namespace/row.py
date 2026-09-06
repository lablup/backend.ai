from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.object_storage import ObjectStorageRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("StorageNamespaceRow",)


def _get_storage_namespace_join_cond() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.object_storage import ObjectStorageRow

    return foreign(StorageNamespaceRow.storage_id) == ObjectStorageRow.id


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

    object_storage_row: Mapped[ObjectStorageRow] = relationship(
        "ObjectStorageRow",
        primaryjoin=_get_storage_namespace_join_cond,
    )

    def to_dataclass(self) -> StorageNamespaceData:
        return StorageNamespaceData(
            id=StorageNamespaceID(self.id),
            storage_id=self.storage_id,
            namespace=self.namespace,
        )
