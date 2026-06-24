"""Query conditions for Reservoir registry repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow


class ReservoirRegistryConditions:
    """Query conditions for Reservoir registries."""

    @staticmethod
    def by_ids(registry_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReservoirRegistryRow.id.in_(registry_ids)

        return inner
