from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
    from ai.backend.manager.models.object_storage import ObjectStorageRow
    from ai.backend.manager.models.vfs_storage import VFSStorageRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: Sequence[str] = ("AssociationArtifactsStorageRow",)


def _get_association_artifact_join_cond() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow

    return ArtifactRevisionRow.id == foreign(AssociationArtifactsStorageRow.artifact_revision_id)


def _get_association_object_storage_join_cond() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.object_storage import ObjectStorageRow

    return ObjectStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


def _get_association_vfs_storage_join_cond() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.vfs_storage import VFSStorageRow

    return VFSStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


class AssociationArtifactsStorageRow(Base):  # type: ignore[misc]
    """
    Association table for linking artifacts to storage namespace.
    """

    __tablename__ = "association_artifacts_storages"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_revision_id", name="uq_artifact_revision_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    artifact_revision_id: Mapped[uuid.UUID] = mapped_column(
        "artifact_revision_id",
        GUID,
        nullable=False,
    )
    storage_namespace_id: Mapped[uuid.UUID] = mapped_column(
        "storage_namespace_id",
        GUID,
        nullable=False,
    )
    storage_type: Mapped[str] = mapped_column("storage_type", sa.String, nullable=False)

    artifact_revision_row: Mapped[ArtifactRevisionRow] = relationship(
        "ArtifactRevisionRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin=_get_association_artifact_join_cond,
    )

    # only valid when storage_type is "object_storage"
    object_storage_row: Mapped[ObjectStorageRow | None] = relationship(
        "ObjectStorageRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin=_get_association_object_storage_join_cond,
        overlaps="vfs_storage_row",
    )

    # only valid when storage_type is "vfs"
    vfs_storage_row: Mapped[VFSStorageRow | None] = relationship(
        "VFSStorageRow",
        back_populates="association_artifacts_storages_rows",
        primaryjoin=_get_association_vfs_storage_join_cond,
        overlaps="object_storage_row",
    )
