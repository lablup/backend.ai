from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.network import NetworkID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.network.types import NetworkData
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class NetworkCreator(EntityCreator[NetworkRow, NetworkData]):
    """Creator for an inter-container network.

    A network is its own scope and joins the project it is created in, which is what
    the RBAC element reference used to say from the call site.
    """

    name: str
    ref_name: str
    driver: str
    domain_name: str
    project_id: ProjectID
    options: Mapping[str, Any]

    @override
    def entity_id(self, row: NetworkRow) -> NetworkID:
        return NetworkID(row.id)

    @override
    def member_of(self, row: NetworkRow) -> Collection[EntityIdentifier]:
        return (ProjectID(self.project_id),)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> NetworkRow:
        return NetworkRow(
            self.name,
            self.ref_name,
            self.driver,
            self.domain_name,
            self.project_id,
            options=self.options,
        )

    @override
    def to_data(self, row: NetworkRow) -> NetworkData:
        return row.to_data()
