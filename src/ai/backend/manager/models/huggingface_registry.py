from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("HuggingFaceRegistryRow",)


def _get_registry_artifact_join_condition():
    from ai.backend.manager.models.artifact import ArtifactRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRow.registry_id)


def _get_registry_meta_join_condition():
    from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

    return HuggingFaceRegistryRow.id == foreign(ArtifactRegistryRow.registry_id)


class HuggingFaceRegistryRow(Base):
    __tablename__ = "huggingface_registries"

    id = IDColumn("id")
    url = sa.Column("url", sa.String, nullable=False)
    token = sa.Column("token", sa.String, nullable=True, default=None)

    artifacts = relationship(
        "ArtifactRow",
        back_populates="huggingface_registry",
        primaryjoin=_get_registry_artifact_join_condition,
        viewonly=True,
    )
    meta = relationship(
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
        try:
            return HuggingFaceRegistryData(
                id=self.id, name=self.meta.name, url=self.url, token=self.token
            )
        except Exception:
            raise RelationNotLoadedError()
