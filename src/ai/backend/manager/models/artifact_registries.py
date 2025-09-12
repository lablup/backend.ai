from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRegistryRow",)


def _get_huggingface_registry_join_condition():
    from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


def _get_reservoir_registry_join_condition():
    from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow

    return ReservoirRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class ArtifactRegistryRow(Base):
    """
    Common information of all artifact_registry records.
    """

    __tablename__ = "artifact_registries"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, nullable=False, unique=True)
    registry_id = sa.Column("registry_id", GUID, nullable=False, unique=True)
    type = sa.Column("type", sa.String, nullable=False)

    huggingface_registries = relationship(
        "HuggingFaceRegistryRow",
        back_populates="meta",
        primaryjoin=_get_huggingface_registry_join_condition,
        uselist=False,
        viewonly=True,
    )
    reservoir_registries = relationship(
        "ReservoirRegistryRow",
        back_populates="meta",
        primaryjoin=_get_reservoir_registry_join_condition,
        uselist=False,
        viewonly=True,
    )

    def __str__(self) -> str:
        return f"ArtifactRegistryRow(id={self.id}, registry_id={self.registry_id}, type={self.type}, name={self.name})"

    def to_dataclass(self) -> ArtifactRegistryData:
        return ArtifactRegistryData(
            id=self.id,
            registry_id=self.registry_id,
            name=self.name,
            type=ArtifactRegistryType(self.type),
        )
