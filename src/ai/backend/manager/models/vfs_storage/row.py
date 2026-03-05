from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.types import ArtifactStorageId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.models.base import (
    GUID,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("VFSStorageRow",)


def _get_vfs_storage_association_artifact_join_cond() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )

    return VFSStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


class VFSStorageRow(ArtifactStorageRow):
    """
    Represents a VFS storage configuration.
    This model is used to store the details of VFS storage backends
    such as base paths, subpaths, and chunk sizes.
    Uses SQLAlchemy Joined Table Inheritance (child of ArtifactStorageRow).
    """

    __tablename__ = "vfs_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, sa.ForeignKey("artifact_storages.id", ondelete="CASCADE"), primary_key=True
    )
    host: Mapped[str] = mapped_column("host", sa.String, nullable=False)
    base_path: Mapped[str] = mapped_column("base_path", sa.String, nullable=False)

    association_artifacts_storages_rows: Mapped[list[AssociationArtifactsStorageRow]] = (
        relationship(
            "AssociationArtifactsStorageRow",
            back_populates="vfs_storage_row",
            primaryjoin=_get_vfs_storage_association_artifact_join_cond,
            overlaps="association_artifacts_storages_rows,object_storage_row",
            viewonly=True,
        )
    )

    __mapper_args__ = {
        "polymorphic_identity": "vfs_storage",
    }

    def __str__(self) -> str:
        return f"VFSStorageRow(id={self.id}, host={self.host}, base_path={self.base_path})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> VFSStorageData:
        return VFSStorageData(
            id=ArtifactStorageId(self.id),
            name=self.name,
            type=ArtifactStorageType(self.type),
            host=self.host,
            base_path=Path(self.base_path),
        )
