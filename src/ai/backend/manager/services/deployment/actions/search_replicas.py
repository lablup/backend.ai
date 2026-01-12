from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class SearchReplicasAction(DeploymentBaseAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_replicas"


@dataclass
class SearchReplicasActionResult(BaseActionResult):
    data: list[ModelReplicaData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
