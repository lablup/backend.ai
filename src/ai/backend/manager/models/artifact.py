from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
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


def _get_artifact_revision_join_cond():
    from .artifact_revision import ArtifactRevisionRow

    return foreign(ArtifactRevisionRow.artifact_id) == ArtifactRow.id


class ArtifactRow(Base):
    """
    Represents an artifact in the system.
    Artifacts can be models, packages, or images.
    This model is used to track the metadata of artifacts.
    """

    __tablename__ = "artifacts"

    id = IDColumn("id")
    type = sa.Column("type", sa.Enum(ArtifactType), index=True, nullable=False)
    name = sa.Column("name", sa.String, index=True, nullable=False)
    registry_id = sa.Column("registry_id", GUID, nullable=False, index=True)
    registry_type = sa.Column("registry_type", sa.String, nullable=False, index=True)
    source_registry_id = sa.Column("source_registry_id", GUID, nullable=False, index=True)
    source_registry_type = sa.Column("source_registry_type", sa.String, nullable=False, index=True)
    description = sa.Column("description", sa.String, nullable=True)

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

    revision_rows = relationship(
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
            f"description={self.description})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ArtifactData:
        return ArtifactData(
            id=self.id,
            type=self.type,
            name=self.name,
            registry_id=self.registry_id,
            registry_type=self.registry_type,
            source_registry_id=self.source_registry_id,
            source_registry_type=self.source_registry_type,
            description=self.description,
        )

    def to_dataclass_with_revisions(self) -> ArtifactDataWithRevisions:
        return ArtifactDataWithRevisions(
            artifact=ArtifactData(
                id=self.id,
                type=self.type,
                name=self.name,
                registry_id=self.registry_id,
                registry_type=self.registry_type,
                source_registry_id=self.source_registry_id,
                source_registry_type=self.source_registry_type,
                description=self.description,
                authorized=self.authorized,
            ),
            revisions=[
                ArtifactRevisionData(
                    id=revision.id,
                    artifact_id=revision.artifact_id,
                    version=revision.version,
                    readme=revision.readme,
                    size=revision.size,
                    status=ArtifactStatus(revision.status),
                    created_at=revision.created_at,
                    updated_at=revision.updated_at,
                )
                for revision in self.revision_rows
            ],
        )
