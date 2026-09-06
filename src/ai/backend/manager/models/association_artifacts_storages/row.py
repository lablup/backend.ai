from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: Sequence[str] = ("AssociationArtifactsStorageRow",)


class AssociationArtifactsStorageRow(Base):
    """
    Association table for linking artifacts to storage namespace.
    """

    __tablename__ = "association_artifacts_storages"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_revision_id", name="uq_artifact_revision_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    artifact_revision_id: Mapped[ArtifactRevisionID] = mapped_column(
        "artifact_revision_id",
        GUID(ArtifactRevisionID),
        nullable=False,
    )
    storage_namespace_id: Mapped[StorageNamespaceID] = mapped_column(
        "storage_namespace_id",
        GUID(StorageNamespaceID),
        nullable=False,
    )
    storage_type: Mapped[str] = mapped_column("storage_type", sa.String, nullable=False)
