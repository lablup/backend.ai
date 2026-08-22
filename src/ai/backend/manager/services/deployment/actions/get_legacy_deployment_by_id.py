from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import LegacyDeploymentData
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
)


@dataclass
class GetLegacyDeploymentByIdAction(DeploymentSingleEntityAction):
    """Legacy (REST v1) get-by-id. Returns the full current revision. DO NOT
    USE in new code — v2 / GraphQL use ``GetDeploymentByIdAction``.
    """

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_legacy_deployment_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetLegacyDeploymentByIdActionResult:
    data: LegacyDeploymentData
