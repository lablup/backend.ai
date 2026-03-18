"""Query conditions for deployment policies."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.repositories.base import QueryCondition


class DeploymentPolicyConditions:
    """Query conditions for deployment policies."""

    @staticmethod
    def by_ids(policy_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentPolicyRow.id.in_(policy_ids)

        return inner

    @staticmethod
    def by_endpoint_ids(endpoint_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentPolicyRow.endpoint.in_(endpoint_ids)

        return inner
