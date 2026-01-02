from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
    CreateScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
    PurgeScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors(AbstractProcessorPackage):
    create_scaling_group: ActionProcessor[CreateScalingGroupAction, CreateScalingGroupActionResult]
    purge_scaling_group: ActionProcessor[PurgeScalingGroupAction, PurgeScalingGroupActionResult]
    search_scaling_groups: ActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]

    def __init__(self, service: ScalingGroupService, action_monitors: list[ActionMonitor]) -> None:
        self.create_scaling_group = ActionProcessor(service.create_scaling_group, action_monitors)
        self.purge_scaling_group = ActionProcessor(service.purge_scaling_group, action_monitors)
        self.search_scaling_groups = ActionProcessor(service.search_scaling_groups, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateScalingGroupAction.spec(),
            PurgeScalingGroupAction.spec(),
            SearchScalingGroupsAction.spec(),
        ]
