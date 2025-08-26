from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ReservoirRegistryRow",)


class ReservoirRegistryRow(Base):
    __tablename__ = "reservoir_registries"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, index=True, unique=True, nullable=False)
    endpoint = sa.Column("endpoint", sa.String, nullable=False)

    def __str__(self) -> str:
        return f"ReservoirRegistryRow(id={self.id}, name={self.name}, endpoint={self.endpoint})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ReservoirRegistryData:
        return ReservoirRegistryData(
            id=self.id,
            name=self.name,
            endpoint=self.endpoint,
        )
