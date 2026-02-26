from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.storage.types import ArtifactStorageData, ArtifactStorageType
from ai.backend.common.types import ArtifactStorageId
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactStorageRow",)


class ArtifactStorageRow(Base):  # type: ignore[misc]
    """
    Common information of all artifact storage records.
    Uses SQLAlchemy Joined Table Inheritance as the base class.
    """

    __tablename__ = "artifact_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, nullable=False, unique=True)
    type: Mapped[str] = mapped_column("type", sa.String, nullable=False)

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "base",
    }

    def __str__(self) -> str:
        return f"ArtifactStorageRow(id={self.id}, type={self.type}, name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ArtifactStorageData:
        return ArtifactStorageData(
            id=ArtifactStorageId(self.id),
            name=self.name,
            type=ArtifactStorageType(self.type),
        )
