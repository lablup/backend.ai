from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.repositories.base import QueryCondition


class ArtifactRegistryConditions:
    """Query conditions for artifact registries."""

    @staticmethod
    def by_ids(registry_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRegistryRow.id.in_(registry_ids)

        return inner
