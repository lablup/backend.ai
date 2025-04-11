from ai.backend.manager.actions.processor import ActionProcessor
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


class GroupProcessors:
    create_group: ActionProcessor[CreateGroupAction, CreateGroupActionResult]
    modify_group: ActionProcessor[ModifyGroupAction, ModifyGroupActionResult]
    delete_group: ActionProcessor[DeleteGroupAction, DeleteGroupActionResult]
    purge_group: ActionProcessor[PurgeGroupAction, PurgeGroupActionResult]
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]

    def __init__(self, group_service: GroupService) -> None:
        self.create_group = ActionProcessor(group_service.create_group)
        self.modify_group = ActionProcessor(group_service.modify_group)
        self.delete_group = ActionProcessor(group_service.delete_group)
        self.purge_group = ActionProcessor(group_service.purge_group)
        self.usage_per_month = ActionProcessor(group_service.usage_per_month)
        self.usage_per_period = ActionProcessor(group_service.usage_per_period)
