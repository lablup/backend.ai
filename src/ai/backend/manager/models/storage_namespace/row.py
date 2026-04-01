from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

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


class StorageNamespaceRow(Base):  # type: ignore[misc]
    __tablename__ = "storage_namespace"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("storage_id", "namespace", name="uq_storage_id_namespace"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    storage_id: Mapped[uuid.UUID] = mapped_column(
        "storage_id",
        GUID,
        nullable=False,
    )
    namespace: Mapped[str] = mapped_column("namespace", sa.String, nullable=False)

    object_storage_row: Mapped[ObjectStorageRow] = relationship(
        "ObjectStorageRow",
        back_populates="namespace_rows",
        primaryjoin=_get_storage_namespace_join_cond,
    )

    def to_dataclass(self) -> StorageNamespaceData:
        return StorageNamespaceData(
            id=self.id,
            storage_id=self.storage_id,
            namespace=self.namespace,
        )
