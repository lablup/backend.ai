from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class GlobalSearchReplicasAction(DeploymentGlobalAction):
    """Page through replicas across every deployment."""

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_replicas"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GlobalSearchReplicasActionResult:
    data: list[ModelReplicaData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
