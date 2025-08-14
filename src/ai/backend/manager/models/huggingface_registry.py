from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("HuggingFaceRegistryRow",)


class HuggingFaceRegistryRow(Base):
    __tablename__ = "huggingface_registries"

    id = IDColumn("id")
    url = sa.Column("url", sa.String, nullable=False)
    name = sa.Column("name", sa.String, nullable=False, unique=True)
    token = sa.Column("token", sa.String, nullable=True, default=None)

    def __str__(self) -> str:
        return f"HuggingFaceRegistryRow(id={self.id}, url={self.url}, name={self.name}, token={self.token})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> HuggingFaceRegistryData:
        return HuggingFaceRegistryData(id=self.id, url=self.url, name=self.name, token=self.token)
