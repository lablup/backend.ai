from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.artifact_registry import ArtifactType
from ai.backend.manager.data.artifact.types import ArtifactData
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
    size = sa.Column("size", sa.BigInteger, nullable=False, default=0)
    registry_id = sa.Column("registry_id", GUID, nullable=False, index=True)
    registry_type = sa.Column("registry_type", sa.String, nullable=False, index=True)
    source_registry_id = sa.Column("source_registry_id", GUID, nullable=True, index=True)
    description = sa.Column("description", sa.String, nullable=True)
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
            f"description={self.description}, "
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()}, "
            f"authorized={self.authorized}, "
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
            source_registry_id=self.source_registry_id,
            registry_id=self.registry_id,
            registry_type=self.registry_type,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            authorized=self.authorized,
            version=self.version,
        )
