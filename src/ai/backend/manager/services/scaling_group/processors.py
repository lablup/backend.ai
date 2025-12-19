from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.modify import (
    ModifyScalingGroupAction,
    ModifyScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors(AbstractProcessorPackage):
    modify_scaling_group: ActionProcessor[ModifyScalingGroupAction, ModifyScalingGroupActionResult]
    search_scaling_groups: ActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]

    def __init__(self, service: ScalingGroupService, action_monitors: list[ActionMonitor]) -> None:
        self.modify_scaling_group = ActionProcessor(service.modify_scaling_group, action_monitors)
        self.search_scaling_groups = ActionProcessor(service.search_scaling_groups, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ModifyScalingGroupAction.spec(),
            SearchScalingGroupsAction.spec(),
        ]
