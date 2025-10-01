from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRevisionRow",)


def _get_artifact_join_cond():
    from .artifact import ArtifactRow

    return foreign(ArtifactRevisionRow.artifact_id) == ArtifactRow.id


class ArtifactRevisionRow(Base):
    __tablename__ = "artifact_revisions"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_id_version"),
    )

    id = IDColumn("id")
    artifact_id = sa.Column(
        GUID,
        nullable=False,
        index=True,
    )
    version = sa.Column("version", sa.String, nullable=False)
    readme = sa.Column("readme", sa.TEXT, nullable=True, default=None)
    size = sa.Column("size", sa.BigInteger, nullable=True, default=None)

    # It's unnatural to include "status" in the revision, but let's put it here for now instead of creating separate table.
    status = sa.Column(sa.String, index=True, nullable=False, default=ArtifactStatus.SCANNED.value)
    remote_status = sa.Column(
        sa.String, index=True, nullable=True, default=None, server_default=sa.null()
    )

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
        index=True,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
        index=True,
    )

    artifact = relationship(
        "ArtifactRow",
        back_populates="revision_rows",
        primaryjoin=_get_artifact_join_cond,
        viewonly=True,
    )

    association_artifacts_storages_rows = relationship(
        "AssociationArtifactsStorageRow",
        back_populates="artifact_revision_row",
        primaryjoin=lambda: ArtifactRevisionRow.id
        == foreign(AssociationArtifactsStorageRow.artifact_revision_id),
    )

    def __str__(self) -> str:
        return (
            f"ArtifactRevisionRow("
            f"id={self.id}, "
            f"artifact_id={self.artifact_id}, "
            f"version={self.version}, "
            f"readme={self.readme[:15]}, "  # truncate for display
            f"size={self.size}, "
            f"status={self.status}, "
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()})"
        )

    def to_dataclass(self) -> ArtifactRevisionData:
        return ArtifactRevisionData(
            id=self.id,
            artifact_id=self.artifact_id,
            version=self.version,
            readme=self.readme,
            size=self.size,
            status=ArtifactStatus(self.status),
            remote_status=ArtifactRemoteStatus(self.remote_status) if self.remote_status else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_huggingface_model_data(
        cls,
        artifact_id: uuid.UUID,
        model_data: ModelData,
    ) -> ArtifactRevisionRow:
        return cls(
            artifact_id=artifact_id,
            version=model_data.revision,
            readme=model_data.readme,
            size=model_data.size,
            status=ArtifactStatus.SCANNED.value,
            created_at=model_data.created_at,
            updated_at=model_data.modified_at,
        )
