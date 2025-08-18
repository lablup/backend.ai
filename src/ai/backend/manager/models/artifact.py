from __future__ import annotations

import logging
import uuid
from typing import Optional, Self

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRow",)


class ArtifactRow(Base):
    """
    Represents an artifact in the system.
    Artifacts can be models, packages, or images.
    This model is used to track the metadata of artifacts
    """

    __tablename__ = "artifacts"

    id = IDColumn("id")
    type = sa.Column("type", sa.Enum(ArtifactType), index=True, nullable=False)
    name = sa.Column("name", sa.String, index=True, nullable=False)
    size = sa.Column("size", sa.BigInteger, nullable=True, default=None)
    registry_id = sa.Column("registry_id", GUID, nullable=False, index=True)
    registry_type = sa.Column("registry_type", sa.String, nullable=False, index=True)
    source_registry_id = sa.Column("source_registry_id", GUID, nullable=True, index=True)
    source_registry_type = sa.Column("source_registry_type", sa.String, nullable=True, index=True)
    description = sa.Column("description", sa.String, nullable=True)
    readme = sa.Column("readme", sa.TEXT, nullable=True)
    version = sa.Column("version", sa.String, nullable=False)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        index=True,
    )
    authorized = sa.Column(sa.Boolean, nullable=False, default=False)
    status = sa.Column(sa.String, nullable=False, default=ArtifactStatus.SCANNED.value)

    association_artifacts_storages_rows = relationship(
        "AssociationArtifactsStorageRow",
        back_populates="artifact_row",
        primaryjoin=lambda: ArtifactRow.id == foreign(AssociationArtifactsStorageRow.artifact_id),
    )

    huggingface_registry = relationship(
        "HuggingFaceRegistryRow",
        back_populates="artifacts",
        primaryjoin=lambda: foreign(ArtifactRow.registry_id) == HuggingFaceRegistryRow.id,
    )

    def __str__(self) -> str:
        return (
            f"ArtifactRow("
            f"id={self.id}, "
            f"type={self.type}, "
            f"name={self.name}, "
            f"size={self.size}, "
            f"registry_id={self.registry_id}, "
            f"registry_type={self.registry_type}, "
            f"source_registry_id={self.source_registry_id}, "
            f"source_registry_type={self.source_registry_type}, "
            f"description={self.description}, "
            f"readme={self.readme[:30]}, "  # truncate for display
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()}, "
            f"authorized={self.authorized}, "
            f"status={self.status}, "
            f"version={self.version})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ArtifactData:
        return ArtifactData(
            id=self.id,
            type=self.type,
            name=self.name,
            size=self.size,
            registry_id=self.registry_id,
            registry_type=self.registry_type,
            source_registry_id=self.source_registry_id,
            source_registry_type=self.source_registry_type,
            description=self.description,
            readme=self.readme,
            created_at=self.created_at,
            updated_at=self.updated_at,
            authorized=self.authorized,
            version=self.version,
            status=ArtifactStatus(self.status),
        )

    @classmethod
    def from_huggingface_model_data(
        cls,
        model_data: ModelData,
        registry_id: uuid.UUID,
        source_registry_id: Optional[uuid.UUID] = None,
        source_registry_type: Optional[ArtifactRegistryType] = None,
    ) -> Self:
        return cls(
            type=ArtifactType.MODEL,
            name=model_data.id,
            size=None,  # Size is populated later when handling ModelImportDone event
            registry_id=registry_id,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_id=source_registry_id,
            source_registry_type=source_registry_type,
            # TODO: How to handle this?
            description="",
            readme="",
            created_at=model_data.created_at,
            updated_at=model_data.modified_at,
            authorized=False,
            version=model_data.revision,
            status=ArtifactStatus.SCANNED.value,
        )
