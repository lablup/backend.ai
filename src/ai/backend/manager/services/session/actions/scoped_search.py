"""Session search over the scopes sessions are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.scopes import (
    DomainSessionOperationScope,
    ProjectSessionOperationScope,
    UserSessionOperationScope,
)
from ai.backend.manager.models.session.searchers import SessionSearcher

__all__ = (
    "DomainSessionScopeItem",
    "ProjectSessionScopeItem",
    "ScopedSearchSessionsAction",
    "SessionScopeItem",
    "UserSessionScopeItem",
)


class SessionScopeItem(ScopeItem, ABC):
    """One side a session is reachable from."""


@dataclass(frozen=True)
class DomainSessionScopeItem(SessionScopeItem):
    """The sessions of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def operation_scope(self) -> OperationScope:
        return DomainSessionOperationScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class UserSessionScopeItem(SessionScopeItem):
    """The sessions one user holds."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserSessionOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class ProjectSessionScopeItem(SessionScopeItem):
    """The sessions of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectSessionOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class ScopedSearchSessionsAction(OperationScopeOpsAction[SessionRow, SessionEntityData]):
    """Page through the sessions the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[SessionScopeItem]
    searcher: SessionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_sessions"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> SessionSearcher:
        return self.searcher
