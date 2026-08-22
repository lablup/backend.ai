from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class SearchHuggingFaceRegistriesAction(ArtifactRegistryAction):
    """Action to search HuggingFace registries."""

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_hugging_face_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchHuggingFaceRegistriesActionResult:
    """Result of searching HuggingFace registries."""

    registries: list[HuggingFaceRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
