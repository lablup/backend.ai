from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.artifact.types import (
    ArtifactStatus,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

log = StructuredLogger(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRevisionRow",)


class ArtifactRevisionRow(Base):
    __tablename__ = "artifact_revisions"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_id_version"),
    )

    id: Mapped[ArtifactRevisionID] = mapped_column(
        "id",
        GUID(ArtifactRevisionID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    artifact_id: Mapped[ArtifactID] = mapped_column(
        "artifact_id",
        GUID(ArtifactID),
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

    @override
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
