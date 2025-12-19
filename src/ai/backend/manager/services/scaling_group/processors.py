from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.purge import (
    PurgeScalingGroupAction,
    PurgeScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors(AbstractProcessorPackage):
    search_scaling_groups: ActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]
    purge_scaling_group: ActionProcessor[PurgeScalingGroupAction, PurgeScalingGroupActionResult]

    def __init__(self, service: ScalingGroupService, action_monitors: list[ActionMonitor]) -> None:
        self.search_scaling_groups = ActionProcessor(service.search_scaling_groups, action_monitors)
        self.purge_scaling_group = ActionProcessor(service.purge_scaling_group, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            SearchScalingGroupsAction.spec(),
            PurgeScalingGroupAction.spec(),
        ]
