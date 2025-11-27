from __future__ import annotations

import logging
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.vfs_storage.types import VFSStorageData
from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("VFSStorageRow",)


def _get_vfs_storage_association_artifact_join_cond():
    return VFSStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


def _get_vfs_storage_meta_join_cond():
    from .artifact_storages import ArtifactStorageRow

    return VFSStorageRow.id == foreign(ArtifactStorageRow.storage_id)


class VFSStorageRow(Base):
    """
    Represents a VFS storage configuration.
    This model is used to store the details of VFS storage backends
    such as base paths, subpaths, and chunk sizes.
    """

    __tablename__ = "vfs_storages"

    id = IDColumn("id")
    host = sa.Column("host", sa.String, nullable=False)
    base_path = sa.Column("base_path", sa.String, nullable=False)

    association_artifacts_storages_rows = relationship(
        "AssociationArtifactsStorageRow",
        back_populates="vfs_storage_row",
        primaryjoin=_get_vfs_storage_association_artifact_join_cond,
        overlaps="association_artifacts_storages_rows,object_storage_row",
    )
    meta = relationship(
        "ArtifactStorageRow",
        back_populates="vfs_storages",
        primaryjoin=_get_vfs_storage_meta_join_cond,
        uselist=False,
        viewonly=True,
    )

    def __str__(self) -> str:
        return f"VFSStorageRow(id={self.id}, host={self.host}, base_path={self.base_path})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> VFSStorageData:
        try:
            return VFSStorageData(
                id=self.id,
                name=self.meta.name,
                host=self.host,
                base_path=Path(self.base_path),
            )
        except Exception:
            raise RelationNotLoadedError()
