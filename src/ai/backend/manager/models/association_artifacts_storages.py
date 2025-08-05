from __future__ import annotations

import logging
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.logging import BraceStyleAdapter

from .base import GUID, Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationArtifactsStorageRow",)


class AssociationArtifactsStorageRow(Base):
    """
    Association table for linking artifacts to object storages.
    """

    __tablename__ = "association_artifacts_storages"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_id", "storage_id", name="uq_artifact_id_storage_id"),
    )

    id = IDColumn()
    artifact_id = sa.Column(
        "artifact_id",
        GUID,
        nullable=False,
    )
    storage_id = sa.Column(
        "storage_id",
        GUID,
        nullable=False,
    )

    artifact_row = relationship(
        "ArtifactRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin="ArtifactRow.id == foreign(AssociationArtifactsStorageRow.artifact_id)",
    )
    storage_row = relationship(
        "ObjectStorageRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin="ObjectStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_id)",
    )
