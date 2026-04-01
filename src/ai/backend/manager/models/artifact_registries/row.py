from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
    from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRegistryRow",)


def _get_huggingface_registry_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


def _get_reservoir_registry_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow

    return ReservoirRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class ArtifactRegistryRow(Base):  # type: ignore[misc]
    """
    Common information of all artifact_registry records.
    """

    __tablename__ = "artifact_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, nullable=False, unique=True)
    registry_id: Mapped[uuid.UUID] = mapped_column("registry_id", GUID, nullable=False, unique=True)
    type: Mapped[str] = mapped_column("type", sa.String, nullable=False)

    huggingface_registries: Mapped[HuggingFaceRegistryRow | None] = relationship(
        "HuggingFaceRegistryRow",
        back_populates="meta",
        primaryjoin=_get_huggingface_registry_join_condition,
        uselist=False,
        viewonly=True,
    )
    reservoir_registries: Mapped[ReservoirRegistryRow | None] = relationship(
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
