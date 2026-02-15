from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.artifact_storages.types import ArtifactStorageData
    from ai.backend.manager.models.object_storage import ObjectStorageRow
    from ai.backend.manager.models.vfs_storage import VFSStorageRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactStorageRow",)


def _get_object_storage_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.object_storage import ObjectStorageRow

    return ObjectStorageRow.id == foreign(ArtifactStorageRow.storage_id)


def _get_vfs_storage_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.vfs_storage import VFSStorageRow

    return VFSStorageRow.id == foreign(ArtifactStorageRow.storage_id)


class ArtifactStorageRow(Base):  # type: ignore[misc]
    """
    Common information of all artifact storage records.
    """

    __tablename__ = "artifact_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, nullable=False, unique=True)
    storage_id: Mapped[uuid.UUID] = mapped_column("storage_id", GUID, nullable=False, unique=True)
    type: Mapped[str] = mapped_column("type", sa.String, nullable=False)

    object_storages: Mapped[ObjectStorageRow | None] = relationship(
        "ObjectStorageRow",
        back_populates="meta",
        primaryjoin=_get_object_storage_join_condition,
        uselist=False,
        viewonly=True,
    )
    vfs_storages: Mapped[VFSStorageRow | None] = relationship(
        "VFSStorageRow",
        back_populates="meta",
        primaryjoin=_get_vfs_storage_join_condition,
        uselist=False,
        viewonly=True,
    )

    def __str__(self) -> str:
        return f"ArtifactStorageRow(id={self.id}, storage_id={self.storage_id}, type={self.type}, name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ArtifactStorageData:
        from ai.backend.common.types import ArtifactStorageId, ConcreteStorageId
        from ai.backend.manager.data.artifact_storages.types import ArtifactStorageData

        return ArtifactStorageData(
            id=ArtifactStorageId(self.id),
            name=self.name,
            storage_id=ConcreteStorageId(self.storage_id),
            type=ArtifactStorageType(self.type),
        )
