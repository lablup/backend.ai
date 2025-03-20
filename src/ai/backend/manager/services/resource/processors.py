from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.resource.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.resource.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.resource.actions.usage_per_period import UsagePerPeriodAction, UsagePerPeriodActionResult
from ai.backend.manager.services.resource.service import ResourceService


class ResourceProcessors:
    list_presets: ActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]
    check_presets: ActionProcessor[CheckResourcePresetsAction, CheckResourcePresetsActionResult]
    recalculate_usage: ActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]

    def __init__(self, service: ResourceService) -> None:
        self.list_presets = ActionProcessor(service.list_presets)
        self.check_presets = ActionProcessor(service.check_presets)
        self.recalculate_usage = ActionProcessor(service.recalculate_usage)
        self.usage_per_month = ActionProcessor(service.usage_per_month)
        self.usage_per_period = ActionProcessor(service.usage_per_period)