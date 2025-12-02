from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactStorageRow",)


def _get_object_storage_join_condition():
    from ai.backend.manager.models.object_storage import ObjectStorageRow

    return ObjectStorageRow.id == foreign(ArtifactStorageRow.storage_id)


def _get_vfs_storage_join_condition():
    from ai.backend.manager.models.vfs_storage import VFSStorageRow

    return VFSStorageRow.id == foreign(ArtifactStorageRow.storage_id)


class ArtifactStorageRow(Base):
    """
    Common information of all artifact storage records.
    """

    __tablename__ = "artifact_storages"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, nullable=False, unique=True)
    storage_id = sa.Column("storage_id", GUID, nullable=False, unique=True)
    type = sa.Column("type", sa.String, nullable=False)

    object_storages = relationship(
        "ObjectStorageRow",
        back_populates="meta",
        primaryjoin=_get_object_storage_join_condition,
        uselist=False,
        viewonly=True,
    )
    vfs_storages = relationship(
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
