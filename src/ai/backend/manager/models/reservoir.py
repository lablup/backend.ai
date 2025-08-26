from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.reservoir.types import ReservoirData

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ReservoirRow",)


class ReservoirRow(Base):
    """ """

    __tablename__ = "reservoirs"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, index=True, unique=True, nullable=False)
    endpoint = sa.Column("endpoint", sa.String, nullable=False)

    def __str__(self) -> str:
        return f"ReservoirRow(id={self.id}, name={self.name}, endpoint={self.endpoint})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ReservoirData:
        return ReservoirData(
            id=self.id,
            name=self.name,
            endpoint=self.endpoint,
        )
