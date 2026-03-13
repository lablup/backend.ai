from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact.actions.base import (
    ArtifactScopeAction,
    ArtifactScopeActionResult,
)


@dataclass
class SearchArtifactsAction(ArtifactScopeAction):
    querier: BatchQuerier
    _scope_type: ScopeType = field(default=ScopeType.DOMAIN)
    _scope_id: str = field(default="")

    @override
    def entity_id(self) -> str | None:
        return None

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


@dataclass
class SearchArtifactsActionResult(ArtifactScopeActionResult):
    data: list[ArtifactData]
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
