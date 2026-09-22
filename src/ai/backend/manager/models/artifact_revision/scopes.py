"""Operation scopes for artifact revisions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget


@dataclass(frozen=True)
class ArtifactRevisionTarget(ScopeTarget):
    """The revisions one artifact holds."""

    artifact_id: ArtifactID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.artifact_id

    @override
    def to_condition(self) -> QueryCondition:
        artifact_id = self.artifact_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ArtifactRevisionRow.artifact_id == artifact_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
