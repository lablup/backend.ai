from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)
from ai.backend.manager.services.group.service import GroupService


class GroupProcessors(AbstractProcessorPackage):
    create_group: ActionProcessor[CreateGroupAction, CreateGroupActionResult]
    modify_group: ActionProcessor[ModifyGroupAction, ModifyGroupActionResult]
    delete_group: ActionProcessor[DeleteGroupAction, DeleteGroupActionResult]
    purge_group: ActionProcessor[PurgeGroupAction, PurgeGroupActionResult]
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]

    def __init__(self, group_service: GroupService, action_monitors: list[ActionMonitor]) -> None:
        self.create_group = ActionProcessor(group_service.create_group, action_monitors)
        self.modify_group = ActionProcessor(group_service.modify_group, action_monitors)
        self.delete_group = ActionProcessor(group_service.delete_group, action_monitors)
        self.purge_group = ActionProcessor(group_service.purge_group, action_monitors)
        self.usage_per_month = ActionProcessor(group_service.usage_per_month, action_monitors)
        self.usage_per_period = ActionProcessor(group_service.usage_per_period, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateGroupAction.spec(),
            ModifyGroupAction.spec(),
            DeleteGroupAction.spec(),
            PurgeGroupAction.spec(),
            UsagePerMonthAction.spec(),
            UsagePerPeriodAction.spec(),
        ]
