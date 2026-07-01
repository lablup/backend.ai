from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentOptions

from .base import ScalingGroupAction


@dataclass(frozen=True)
class ReplaceDefaultDeploymentOptionsAction(ScalingGroupAction):
    """Action to fully replace a resource group's ``default_deployment_options``.

    Admin-only — new deployments created in this resource group snapshot
    the new default; existing deployments are not affected.
    """

    resource_group: ResourceGroupName
    options: DeploymentOptions

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str:
        return str(self.resource_group)


@dataclass(frozen=True)
class ReplaceDefaultDeploymentOptionsActionResult(BaseActionResult):
    """Result of replacing a resource group's ``default_deployment_options``.

    Carries only the refreshed :class:`DeploymentOptions` — callers that
    need the surrounding resource group node are expected to re-fetch it.
    """

    resource_group: ResourceGroupName
    options: DeploymentOptions

    @override
    def entity_id(self) -> str | None:
        return str(self.resource_group)
