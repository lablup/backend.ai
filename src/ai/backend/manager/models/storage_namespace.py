from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.object_storage_namespace.types import StorageNamespaceData

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("StorageNamespaceRow",)


def _get_storage_namespace_join_cond():
    from .object_storage import ObjectStorageRow

    return foreign(StorageNamespaceRow.storage_id) == ObjectStorageRow.id


class StorageNamespaceRow(Base):
    __tablename__ = "storage_namespace"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("storage_id", "namespace", name="uq_storage_id_namespace"),
    )

    id = IDColumn("id")
    storage_id = sa.Column(
        "storage_id",
        GUID,
        nullable=False,
    )
    namespace = sa.Column("namespace", sa.String, nullable=False)

    object_storage_row = relationship(
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
