from __future__ import annotations

import logging
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter

from .base import GUID, Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationArtifactsStorageRow",)


def _get_association_artifact_join_cond():
    from .artifact_revision import ArtifactRevisionRow

    return ArtifactRevisionRow.id == foreign(AssociationArtifactsStorageRow.artifact_revision_id)


def _get_association_object_storage_join_cond():
    from .object_storage import ObjectStorageRow

    return ObjectStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


class AssociationArtifactsStorageRow(Base):
    """
    Association table for linking artifacts to storage namespace.
    """

    __tablename__ = "association_artifacts_storages"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_revision_id", name="uq_artifact_revision_id"),
    )

    id = IDColumn()
    artifact_revision_id = sa.Column(
        "artifact_revision_id",
        GUID,
        nullable=False,
    )
    storage_namespace_id = sa.Column(
        "storage_namespace_id",
        GUID,
        nullable=False,
    )
    storage_type = sa.Column("storage_type", sa.String, nullable=False)

    artifact_revision_row = relationship(
        "ArtifactRevisionRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin=_get_association_artifact_join_cond,
    )

    # only valid when storage_type is "object_storage"
    object_storage_row = relationship(
        "ObjectStorageRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin=_get_association_object_storage_join_cond,
    )
