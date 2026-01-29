from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact import ArtifactRow
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("HuggingFaceRegistryRow",)


def _get_registry_artifact_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.artifact import ArtifactRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRow.registry_id)


def _get_registry_meta_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class HuggingFaceRegistryRow(Base):
    __tablename__ = "huggingface_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    url: Mapped[str] = mapped_column("url", sa.String, nullable=False)
    token: Mapped[str | None] = mapped_column("token", sa.String, nullable=True, default=None)

    artifacts: Mapped[list[ArtifactRow]] = relationship(
        "ArtifactRow",
        back_populates="huggingface_registry",
        primaryjoin=_get_registry_artifact_join_condition,
        viewonly=True,
    )
    meta: Mapped[ArtifactRegistryRow | None] = relationship(
        "ArtifactRegistryRow",
        back_populates="huggingface_registries",
        primaryjoin=_get_registry_meta_join_condition,
        uselist=False,
        viewonly=True,
    )

    def __str__(self) -> str:
        return f"HuggingFaceRegistryRow(id={self.id}, url={self.url}, token={self.token})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> HuggingFaceRegistryData:
        if self.meta is None:
            raise RelationNotLoadedError()
        return HuggingFaceRegistryData(
            id=self.id, name=self.meta.name, url=self.url, token=self.token
        )
