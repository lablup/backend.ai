from ai.backend.manager.actions.processor import ActionProcessor
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
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]

    def __init__(self, service: GroupService) -> None:
        self.usage_per_month = ActionProcessor(service.usage_per_month)
        self.usage_per_period = ActionProcessor(service.usage_per_period)
