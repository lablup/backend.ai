from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ArtifactScopeAction, ArtifactScopeActionResult


@dataclass
class SearchArtifactsWithRevisionsAction(ArtifactScopeAction):
    """Action to search artifacts with their revisions."""

    querier: BatchQuerier
    _scope_type: ScopeType = field(default=ScopeType.DOMAIN)
    _scope_id: str = field(default="")

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def target_element(self) -> RBACElementRef:
        # Map ScopeType to RBACElementType
        element_type_map = {
            ScopeType.DOMAIN: RBACElementType.DOMAIN,
            ScopeType.PROJECT: RBACElementType.PROJECT,
            ScopeType.USER: RBACElementType.USER,
        }
        element_type = element_type_map[self._scope_type]
        return RBACElementRef(element_type, self._scope_id)


@dataclass
class SearchArtifactsWithRevisionsActionResult(ArtifactScopeActionResult):
    """Result of searching artifacts with revisions."""

    data: list[ArtifactDataWithRevisions]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType = field(default=ScopeType.DOMAIN)
    _scope_id: str = field(default="")

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
