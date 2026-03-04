from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.session.base import SessionScopeAction


@dataclass
class SearchSessionsAction(SessionScopeAction):
    """Search sessions within a scope (domain/project).

    RBAC validation checks if the user has READ permission in the target scope.
    _scope_type and _scope_id must be set before RBAC validation (typically USER scope).
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchSessionsActionResult(BaseActionResult):
    data: list[SessionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
