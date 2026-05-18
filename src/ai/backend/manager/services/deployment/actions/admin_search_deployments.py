from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass(frozen=True)
class AdminSearchDeploymentsAction(DeploymentBaseAction):
    """Search every deployment with no scope (superadmin path).

    Routed through ``DeploymentAdminProcessors`` so callers make the
    admin intent explicit; scope-restricted variants live on the regular
    ``DeploymentService`` and ``DeploymentRepository``.
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class AdminSearchDeploymentsActionResult(BaseActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
