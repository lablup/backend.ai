from __future__ import annotations

import enum
import logging

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.logging import BraceStyleAdapter

from .base import (
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
    source = sa.Column("source", sa.String, nullable=True)
    registry = sa.Column("registry", sa.String, nullable=True)
    description = sa.Column("description", sa.String, nullable=True)
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

    def __str__(self) -> str:
        return (
            f"ArtifactRow("
            f"id={self.id}, "
            f"type={self.type}, "
            f"name={self.name}, "
            f"size={self.size}, "
            f"source={self.source}, "
            f"registry={self.registry}, "
            f"description={self.description}, "
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()})"
        )

    def __repr__(self) -> str:
        return self.__str__()
