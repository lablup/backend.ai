"""Operation scopes for routings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget


@dataclass(frozen=True)
class DeploymentReplicaTarget(ScopeTarget):
    """The replicas one deployment holds."""

    deployment_id: DeploymentID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.deployment_id

    @override
    def to_condition(self) -> QueryCondition:
        deployment_id = self.deployment_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.endpoint == deployment_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
