from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class SearchReservoirRegistriesAction(ArtifactRegistryAction):
    """Action to search Reservoir registries."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_reservoir_registries"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchReservoirRegistriesActionResult(BaseActionResult):
    """Result of searching Reservoir registries."""

    registries: list[ReservoirRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
