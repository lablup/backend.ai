from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistryScopeAction,
    ArtifactRegistryScopeActionResult,
)


@dataclass
class SearchReservoirRegistriesAction(ArtifactRegistryScopeAction):
    """Action to search Reservoir registries."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT_REGISTRY, "")


@dataclass
class SearchReservoirRegistriesActionResult(ArtifactRegistryScopeActionResult):
    """Result of searching Reservoir registries."""

    registries: list[ReservoirRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
