"""Operation scopes for deployment revisions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class DeploymentRevisionOperationScope(OperationScope):
    """The revisions one deployment holds."""

    deployment_id: DeploymentID

    @override
    def to_condition(self) -> QueryCondition:
        deployment_id = self.deployment_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.endpoint == deployment_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
