"""Query specs for the domains table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class DomainQuerier(DataQuerier[DomainRow, DomainData]):
    """Reads one domain by its id.

    The table keys on the name, so the id it is read by is the uuid column beside it.
    """

    domain_id: DomainID

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return DomainRow.id

    @override
    def entity_id_value(self) -> DomainID:
        return self.domain_id

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
