"""Session search over the scopes sessions are reachable from."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.scopes import SessionTarget
from ai.backend.manager.models.session.searchers import SessionSearcher

__all__ = ("ScopedSearchSessionsAction",)


@dataclass(frozen=True)
class ScopedSearchSessionsAction(OperationScopeOpsAction[SessionRow, SessionEntityData]):
    """Page through the sessions the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[SessionTarget]
    searcher: SessionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_sessions"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> SessionSearcher:
        return self.searcher
