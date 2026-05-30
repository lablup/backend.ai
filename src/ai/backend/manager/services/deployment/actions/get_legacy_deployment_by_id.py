from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import LegacyDeploymentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class GetLegacyDeploymentByIdAction(DeploymentSingleEntityAction):
    """Legacy (REST v1) get-by-id. Returns the full current revision. DO NOT
    USE in new code — v2 / GraphQL use ``GetDeploymentByIdAction``.
    """

    deployment_id: DeploymentID

    @override
    def target_entity_id(self) -> str:
        return str(self.deployment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.deployment_id))

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetLegacyDeploymentByIdActionResult(DeploymentSingleEntityActionResult):
    data: LegacyDeploymentData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
