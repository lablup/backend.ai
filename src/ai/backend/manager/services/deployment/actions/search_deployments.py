from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import DeploymentBaseAction


@dataclass
class SearchDeploymentsAction(DeploymentBaseAction):
    """Action to search model deployments."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_deployments"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchDeploymentsActionResult(BaseActionResult):
    """Result of searching model deployments."""

    deployments: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
