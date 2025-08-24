from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
    DeleteDeploymentAction,
    DeleteDeploymentActionResult,
    GetDeploymentInfoAction,
    GetDeploymentInfoActionResult,
    ListDeploymentsAction,
    ListDeploymentsActionResult,
    ModifyDeploymentAction,
    ModifyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.services.deployment import DeploymentService


class DeploymentProcessors(AbstractProcessorPackage):
    create_deployment: ActionProcessor[CreateDeploymentAction, CreateDeploymentActionResult]
    delete_deployment: ActionProcessor[DeleteDeploymentAction, DeleteDeploymentActionResult]
    get_deployment_info: ActionProcessor[GetDeploymentInfoAction, GetDeploymentInfoActionResult]
    list_deployments: ActionProcessor[ListDeploymentsAction, ListDeploymentsActionResult]
    modify_deployment: ActionProcessor[ModifyDeploymentAction, ModifyDeploymentActionResult]

    def __init__(self, service: DeploymentService, action_monitors: list[ActionMonitor]) -> None:
        self.create_deployment = ActionProcessor(service.create, action_monitors)
        self.delete_deployment = ActionProcessor(service.delete, action_monitors)
        self.get_deployment_info = ActionProcessor(service.get_info, action_monitors)
        self.list_deployments = ActionProcessor(service.list, action_monitors)
        self.modify_deployment = ActionProcessor(service.modify, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDeploymentAction.spec(),
            DeleteDeploymentAction.spec(),
            GetDeploymentInfoAction.spec(),
            ListDeploymentsAction.spec(),
            ModifyDeploymentAction.spec(),
        ]
