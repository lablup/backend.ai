from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.artifact.types import VerificationStepResult
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
    digest = sa.Column("digest", sa.String, nullable=True, server_default=None, default=None)

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
    verification_result = sa.Column(
        "verification_result", sa.JSON(none_as_null=True), nullable=True, default=None
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
            f"remote_status={self.remote_status}, "
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()}, "
            f"digest={self.digest}"
            f")"
        )

    def to_dataclass(self) -> ArtifactRevisionData:
        # Convert JSON dict back to Pydantic model if present
        verification_result = None
        if self.verification_result is not None:
            try:
                verification_result = VerificationStepResult.model_validate(
                    self.verification_result
                )
            except Exception as e:
                # If validation fails, keep as None
                verification_result = None
                log.warning(
                    "Failed to validate verification_result for ArtifactRevisionRow id={}: {}",
                    self.id,
                    e,
                )

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
            digest=self.digest,
            verification_result=verification_result,
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
            remote_status=None,
            created_at=model_data.created_at,
            updated_at=model_data.modified_at,
            digest=model_data.sha,
            verification_result=None,
        )
