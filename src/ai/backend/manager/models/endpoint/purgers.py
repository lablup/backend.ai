"""Purge specs for the endpoints table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
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


@dataclass
class UserEndpointPurger(EntityBatchPurger[EndpointRow, DeploymentID]):
    """Clears the deployments a user leaves behind; their routings and tokens go
    with them through the FK cascade."""

    user_id: UserID
    lifecycle_stages: Collection[EndpointLifecycle]

    @override
    def entity_id(self, row: EndpointRow) -> EntityIdentifier:
        return row.id

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EndpointRow]]:
        return sa.select(EndpointRow).where(
            EndpointRow.session_owner == self.user_id,
            EndpointRow.lifecycle_stage.in_(self.lifecycle_stages),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EndpointRow) -> DeploymentID:
        return row.id
