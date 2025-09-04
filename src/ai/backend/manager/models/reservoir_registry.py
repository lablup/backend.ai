from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ReservoirRegistryRow",)


def _get_registry_artifact_join_condition():
    from ai.backend.manager.models.artifact import ArtifactRow

    return ReservoirRegistryRow.id == foreign(ArtifactRow.registry_id)


def _get_registry_meta_join_condition():
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

    return ReservoirRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class ReservoirRegistryRow(Base):
    __tablename__ = "reservoir_registries"

    id = IDColumn("id")
    endpoint = sa.Column("endpoint", sa.String, nullable=False)
    access_key = sa.Column("access_key", sa.String, nullable=False)
    secret_key = sa.Column("secret_key", sa.String, nullable=False)
    api_version = sa.Column("api_version", sa.String, nullable=False)

    artifacts = relationship(
        "ArtifactRow",
        back_populates="reservoir_registry",
        primaryjoin=_get_registry_artifact_join_condition,
        viewonly=True,
    )
    meta = relationship(
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
        try:
            return ReservoirRegistryData(
                id=self.id,
                name=self.meta.name,
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                api_version=self.api_version,
            )
        except Exception:
            raise RelationNotLoadedError()
