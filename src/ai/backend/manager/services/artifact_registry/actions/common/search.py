from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.searchers import ArtifactRegistrySearcher
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class SearchArtifactRegistriesAction(ArtifactRegistryAction):
    """Action to search artifact registries."""

    searcher: ArtifactRegistrySearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_artifact_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchArtifactRegistriesActionResult:
    """Result of searching artifact registries."""

    registries: list[ArtifactRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
