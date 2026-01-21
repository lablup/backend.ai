from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class SearchHuggingFaceRegistriesAction(ArtifactRegistryAction):
    """Action to search HuggingFace registries."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_huggingface_registries"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchHuggingFaceRegistriesActionResult(BaseActionResult):
    """Result of searching HuggingFace registries."""

    registries: list[HuggingFaceRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
