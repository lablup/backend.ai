from __future__ import annotations

import enum
import logging

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactData

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRow",)


class ArtifactType(enum.StrEnum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


class ArtifactRow(Base):
    """
    Represents an artifact in the system.
    Artifacts can be models, packages, or images.
    This model is used to track the metadata of artifacts,
    including their type, name, and creation timestamp.
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

    association_artifacts_storages_rows = relationship(
        "AssociationArtifactsStorageRow",
        back_populates="artifact_row",
        primaryjoin="ArtifactRow.id == foreign(AssociationArtifactsStorageRow.artifact_id)",
    )

    huggingface_registry = relationship(
        "HuggingFaceRegistryRow",
        back_populates="artifacts",
        primaryjoin="ArtifactRow.registry_id == foreign(HuggingFaceRegistryRow.id)",
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
            version=self.version,
        )
