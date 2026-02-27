from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base import QueryCondition


class ContainerRegistryConditions:
    """Query conditions for container registries."""

    @staticmethod
    def by_ids(registry_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.id.in_(registry_ids)

        return inner
