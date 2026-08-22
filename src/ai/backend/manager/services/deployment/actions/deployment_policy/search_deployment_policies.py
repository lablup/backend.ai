"""Action for searching deployment policies."""

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class SearchDeploymentPoliciesAction(DeploymentGlobalAction):
    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_policies"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchDeploymentPoliciesActionResult:
    data: list[DeploymentPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
