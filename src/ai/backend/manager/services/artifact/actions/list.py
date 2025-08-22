from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.repositories.artifact.repository import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    PaginationOptions,
)
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class ListArtifactsAction(ArtifactAction):
    pagination: PaginationOptions
    ordering: Optional[ArtifactOrderingOptions] = None
    filters: Optional[ArtifactFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListArtifactsActionResult(BaseActionResult):
    data: list[ArtifactData]
    # Note: Total number of artifacts, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
