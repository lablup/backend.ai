from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentOptions

from .base import ResourceGroupAction


@dataclass(frozen=True)
class ReplaceDefaultDeploymentOptionsAction(ResourceGroupAction):
    """Action to fully replace a resource group's ``default_deployment_options``.

    Admin-only — new deployments created in this resource group snapshot
    the new default; existing deployments are not affected.
    """

    resource_group: ResourceGroupName
    options: DeploymentOptions

    @override
    @classmethod
    def action_name(cls) -> str:
        return "replace_resource_group_default_deployment_options"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class ReplaceDefaultDeploymentOptionsActionResult:
    """Result of replacing a resource group's ``default_deployment_options``.

    Carries only the refreshed :class:`DeploymentOptions` — callers that
    need the surrounding resource group node are expected to re-fetch it.
    """

    resource_group: ResourceGroupName
    options: DeploymentOptions
