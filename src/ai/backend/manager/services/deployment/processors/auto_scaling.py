from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.deployment.actions import (
    CreateAutoScalingRuleAction,
    CreateAutoScalingRuleActionResult,
    DeleteAutoScalingRuleAction,
    DeleteAutoScalingRuleActionResult,
    ModifyAutoScalingRuleAction,
    ModifyAutoScalingRuleActionResult,
)
from ai.backend.manager.services.deployment.services.auto_scaling import AutoScalingService


class AutoScalingProcessors(AbstractProcessorPackage):
    create_auto_scaling_rule: ActionProcessor[
        CreateAutoScalingRuleAction, CreateAutoScalingRuleActionResult
    ]
    delete_auto_scaling_rule: ActionProcessor[
        DeleteAutoScalingRuleAction, DeleteAutoScalingRuleActionResult
    ]
    modify_auto_scaling_rule: ActionProcessor[
        ModifyAutoScalingRuleAction, ModifyAutoScalingRuleActionResult
    ]

    def __init__(self, service: AutoScalingService, action_monitors: list[ActionMonitor]) -> None:
        self.create_auto_scaling_rule = ActionProcessor(service.create_rule, action_monitors)
        self.delete_auto_scaling_rule = ActionProcessor(service.delete_rule, action_monitors)
        self.modify_auto_scaling_rule = ActionProcessor(service.modify_rule, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAutoScalingRuleAction.spec(),
            DeleteAutoScalingRuleAction.spec(),
            ModifyAutoScalingRuleAction.spec(),
        ]
