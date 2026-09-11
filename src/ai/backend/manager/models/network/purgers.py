"""Purge specs for the networks table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.network import NetworkID
from ai.backend.manager.data.network.types import NetworkData
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class NetworkPurger(EntityPurger[NetworkRow, NetworkData]):
    """Removes an inter-container network along with the scope it was."""

    network_id: NetworkID

    @override
    def entity_id(self) -> NetworkID:
        return self.network_id

    @override
    def row_class(self) -> type[NetworkRow]:
        return NetworkRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return NetworkRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: NetworkRow) -> NetworkData:
        return row.to_data()
