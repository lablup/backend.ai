from __future__ import annotations

import logging
import uuid
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ArtifactRegistryRow",)


class ArtifactRegistryRow(Base):
    """
    Common information of all artifact_registry records.
    """

    __tablename__ = "artifact_registries"

    id: Mapped[ArtifactRegistryID] = mapped_column(
        "id",
        GUID(ArtifactRegistryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column("name", sa.String, nullable=False, unique=True)
    registry_id: Mapped[uuid.UUID] = mapped_column("registry_id", GUID, nullable=False, unique=True)
    type: Mapped[str] = mapped_column("type", sa.String, nullable=False)

    @override
    def __str__(self) -> str:
        return f"ArtifactRegistryRow(id={self.id}, registry_id={self.registry_id}, type={self.type}, name={self.name})"
