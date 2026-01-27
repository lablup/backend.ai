from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact import ArtifactRow
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ReservoirRegistryRow",)


def _get_registry_artifact_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.artifact import ArtifactRow

    return ReservoirRegistryRow.id == foreign(ArtifactRow.registry_id)


def _get_registry_meta_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

    return ReservoirRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class ReservoirRegistryRow(Base):
    __tablename__ = "reservoir_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String, nullable=False)
    access_key: Mapped[str] = mapped_column("access_key", sa.String, nullable=False)
    secret_key: Mapped[str] = mapped_column("secret_key", sa.String, nullable=False)
    api_version: Mapped[str] = mapped_column("api_version", sa.String, nullable=False)

    artifacts: Mapped[list[ArtifactRow]] = relationship(
        "ArtifactRow",
        back_populates="reservoir_registry",
        primaryjoin=_get_registry_artifact_join_condition,
        viewonly=True,
    )
    meta: Mapped[ArtifactRegistryRow | None] = relationship(
        "ArtifactRegistryRow",
        back_populates="reservoir_registries",
        primaryjoin=_get_registry_meta_join_condition,
        uselist=False,
        viewonly=True,
    )

    def __str__(self) -> str:
        return f"ReservoirRegistryRow(id={self.id}, endpoint={self.endpoint}, api_version={self.api_version})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ReservoirRegistryData:
        if self.meta is None:
            raise RelationNotLoadedError()
        return ReservoirRegistryData(
            id=self.id,
            name=self.meta.name,
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            api_version=self.api_version,
        )
