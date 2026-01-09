from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRow",)


def _get_artifact_revision_join_cond():
    from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow

    return foreign(ArtifactRevisionRow.artifact_id) == ArtifactRow.id


class ArtifactRow(Base):
    """
    Represents an artifact in the system.
    Artifacts can be models, packages, or images.
    This model is used to track the metadata of artifacts.
    """

    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    type: Mapped[ArtifactType] = mapped_column(
        "type", sa.Enum(ArtifactType), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column("name", sa.String, index=True, nullable=False)
    registry_id: Mapped[uuid.UUID] = mapped_column("registry_id", GUID, nullable=False, index=True)
    registry_type: Mapped[str] = mapped_column(
        "registry_type", sa.String, nullable=False, index=True
    )
    source_registry_id: Mapped[uuid.UUID] = mapped_column(
        "source_registry_id", GUID, nullable=False, index=True
    )
    source_registry_type: Mapped[str] = mapped_column(
        "source_registry_type", sa.String, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column("description", sa.String, nullable=True)
    readonly: Mapped[bool] = mapped_column("readonly", sa.Boolean, default=False, nullable=False)
    extra: Mapped[Any | None] = mapped_column(
        "extra", sa.JSON(none_as_null=True), nullable=True, default=None
    )
    scanned_at: Mapped[datetime] = mapped_column(
        "scanned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    availability: Mapped[str] = mapped_column(
        "availability",
        sa.String,
        nullable=False,
        default=ArtifactAvailability.ALIVE.value,
        server_default=ArtifactAvailability.ALIVE.value,
        index=True,
    )

    huggingface_registry: Mapped[HuggingFaceRegistryRow] = relationship(
        "HuggingFaceRegistryRow",
        back_populates="artifacts",
        primaryjoin=lambda: foreign(ArtifactRow.registry_id) == HuggingFaceRegistryRow.id,
        overlaps="reservoir_registry,artifacts",
    )

    reservoir_registry: Mapped[ReservoirRegistryRow] = relationship(
        "ReservoirRegistryRow",
        back_populates="artifacts",
        primaryjoin=lambda: foreign(ArtifactRow.registry_id) == ReservoirRegistryRow.id,
        overlaps="huggingface_registry,artifacts",
    )

    revision_rows: Mapped[list[ArtifactRevisionRow]] = relationship(
        "ArtifactRevisionRow",
        back_populates="artifact",
        primaryjoin=_get_artifact_revision_join_cond,
    )

    def __str__(self) -> str:
        return (
            f"ArtifactRow("
            f"id={self.id}, "
            f"type={self.type}, "
            f"name={self.name}, "
            f"registry_id={self.registry_id}, "
            f"registry_type={self.registry_type}, "
            f"source_registry_id={self.source_registry_id}, "
            f"source_registry_type={self.source_registry_type}, "
            f"description={self.description}, "
            f"availability={self.availability}, "
            f"scanned_at={self.scanned_at}, "
            f"updated_at={self.updated_at}, "
            f"readonly={self.readonly}, "
            f"extra={self.extra})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ArtifactData:
        return ArtifactData(
            id=self.id,
            type=self.type,
            name=self.name,
            registry_id=self.registry_id,
            registry_type=ArtifactRegistryType(self.registry_type),
            source_registry_id=self.source_registry_id,
            source_registry_type=ArtifactRegistryType(self.source_registry_type),
            description=self.description,
            availability=ArtifactAvailability(self.availability),
            scanned_at=self.scanned_at,
            updated_at=self.updated_at,
            readonly=self.readonly,
            extra=self.extra,
        )
