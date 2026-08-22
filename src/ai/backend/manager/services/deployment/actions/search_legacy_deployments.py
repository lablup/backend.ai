from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import LegacyDeploymentData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class GlobalSearchLegacyDeploymentsAction(DeploymentGlobalAction):
    """Legacy (REST v1) search. Returns the full current revision per item. DO
    NOT USE in new code — v2 / GraphQL use ``GlobalSearchDeploymentsAction``.
    """

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_legacy_deployments"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GlobalSearchLegacyDeploymentsActionResult:
    data: list[LegacyDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
