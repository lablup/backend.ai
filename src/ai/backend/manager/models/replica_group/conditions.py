"""Query conditions for replica group repository."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base import QueryCondition


class ReplicaGroupConditions:
    """Query conditions for replica groups."""

    @staticmethod
    def by_ids(group_ids: Collection[ReplicaGroupID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupRow.id.in_(group_ids)

        return inner

    @staticmethod
    def by_deployment_ids(deployment_ids: Collection[DeploymentID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupRow.deployment_id.in_(deployment_ids)

        return inner

    @staticmethod
    def by_lifecycles(lifecycles: Collection[ReplicaGroupLifecycle]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupRow.lifecycle.in_(lifecycles)

        return inner

    @staticmethod
    def by_scaling_statuses(statuses: Collection[ReplicaGroupScalingStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupRow.scaling_status.in_(statuses)

        return inner
