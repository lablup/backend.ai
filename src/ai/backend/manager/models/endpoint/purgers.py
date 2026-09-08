"""Purge specs for the endpoints table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class DeploymentPurger(EntityPurger[EndpointRow, DeploymentInfo]):
    """Removes a deployment along with the scope it was; its routings and policy go
    with it through the FK cascade."""

    deployment_id: DeploymentID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.deployment_id

    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()
