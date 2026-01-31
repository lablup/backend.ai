from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact import ArtifactRow
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRevisionRow",)


def _get_artifact_join_cond() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.artifact import ArtifactRow

    return foreign(ArtifactRevisionRow.artifact_id) == ArtifactRow.id


def _get_association_artifacts_storages_join_cond() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )

    return ArtifactRevisionRow.id == foreign(AssociationArtifactsStorageRow.artifact_revision_id)


class ArtifactRevisionRow(Base):  # type: ignore[misc]
    __tablename__ = "artifact_revisions"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_id_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        "artifact_id",
        GUID,
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column("version", sa.String, nullable=False)
    readme: Mapped[str | None] = mapped_column("readme", sa.TEXT, nullable=True, default=None)
    size: Mapped[int | None] = mapped_column("size", sa.BigInteger, nullable=True, default=None)
    digest: Mapped[str | None] = mapped_column(
        "digest", sa.String, nullable=True, server_default=None, default=None
    )

    # It's unnatural to include "status" in the revision, but let's put it here for now instead of creating separate table.
    status: Mapped[str] = mapped_column(
        "status", sa.String, index=True, nullable=False, default=ArtifactStatus.SCANNED.value
    )
    remote_status: Mapped[str | None] = mapped_column(
        "remote_status",
        sa.String,
        index=True,
        nullable=True,
        default=None,
        server_default=sa.null(),
    )

    created_at: Mapped[datetime | None] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
        index=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
        index=True,
    )
    verification_result: Mapped[dict[str, Any] | None] = mapped_column(
        "verification_result", sa.JSON(none_as_null=True), nullable=True, default=None
    )

    artifact: Mapped[ArtifactRow] = relationship(
        "ArtifactRow",
        back_populates="revision_rows",
        primaryjoin=_get_artifact_join_cond,
        viewonly=True,
    )

    association_artifacts_storages_rows: Mapped[list[AssociationArtifactsStorageRow]] = (
        relationship(
            "AssociationArtifactsStorageRow",
            back_populates="artifact_revision_row",
            primaryjoin=_get_association_artifacts_storages_join_cond,
        )
    )

    def __str__(self) -> str:
        readme_display = self.readme[:15] if self.readme else None
        created_at_str = self.created_at.isoformat() if self.created_at else None
        updated_at_str = self.updated_at.isoformat() if self.updated_at else None
        return (
            f"ArtifactRevisionRow("
            f"id={self.id}, "
            f"artifact_id={self.artifact_id}, "
            f"version={self.version}, "
            f"readme={readme_display}, "
            f"size={self.size}, "
            f"status={self.status}, "
            f"remote_status={self.remote_status}, "
            f"created_at={created_at_str}, "
            f"updated_at={updated_at_str}, "
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
