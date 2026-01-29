from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.base import (
    GUID,
    Base,
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


class VFSStorageRow(Base):
    """
    Represents a VFS storage configuration.
    This model is used to store the details of VFS storage backends
    such as base paths, subpaths, and chunk sizes.
    """

    __tablename__ = "vfs_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, index=True, unique=True, nullable=False)
    host: Mapped[str] = mapped_column("host", sa.String, nullable=False)
    base_path: Mapped[str] = mapped_column("base_path", sa.String, nullable=False)

    association_artifacts_storages_rows: Mapped[list[AssociationArtifactsStorageRow]] = (
        relationship(
            "AssociationArtifactsStorageRow",
            back_populates="vfs_storage_row",
            primaryjoin=_get_vfs_storage_association_artifact_join_cond,
            overlaps="association_artifacts_storages_rows,object_storage_row",
        )
    )

    def __str__(self) -> str:
        return (
            f"VFSStorageRow("
            f"id={self.id}, "
            f"name={self.name}, "
            f"host={self.host}, "
            f"base_path={self.base_path})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> VFSStorageData:
        return VFSStorageData(
            id=self.id,
            name=self.name,
            host=self.host,
            base_path=Path(self.base_path),
        )
