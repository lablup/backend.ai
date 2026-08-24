from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.searchers import ReservoirRegistrySearcher
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class SearchReservoirRegistriesAction(ArtifactRegistryAction):
    """Action to search Reservoir registries."""

    searcher: ReservoirRegistrySearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_reservoir_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchReservoirRegistriesActionResult:
    """Result of searching Reservoir registries."""

    registries: list[ReservoirRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
