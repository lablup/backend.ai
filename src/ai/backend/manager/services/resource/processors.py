from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.resource.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.resource.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)
from ai.backend.manager.services.resource.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
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
from ai.backend.manager.services.resource.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)
from ai.backend.manager.services.resource.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.resource.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
    WatcherAgentRestartActionResult,
)
from ai.backend.manager.services.resource.actions.watcher_agent_start import (
    WatcherAgentStartAction,
    WatcherAgentStartActionResult,
)
from ai.backend.manager.services.resource.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
    WatcherAgentStopActionResult,
)
from ai.backend.manager.services.resource.service import ResourceService


class ResourceProcessors:
    list_presets: ActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]
    check_presets: ActionProcessor[CheckResourcePresetsAction, CheckResourcePresetsActionResult]
    recalculate_usage: ActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]
    usage_per_month: ActionProcessor[UsagePerMonthAction, UsagePerMonthActionResult]
    usage_per_period: ActionProcessor[UsagePerPeriodAction, UsagePerPeriodActionResult]
    user_month_stats: ActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: ActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]
    get_watcher_status: ActionProcessor[GetWatcherStatusAction, GetWatcherStatusActionResult]
    watcher_agent_start: ActionProcessor[WatcherAgentStartAction, WatcherAgentStartActionResult]
    watcher_agent_restart: ActionProcessor[
        WatcherAgentRestartAction, WatcherAgentRestartActionResult
    ]
    watcher_agent_stop: ActionProcessor[WatcherAgentStopAction, WatcherAgentStopActionResult]
    get_container_registries: ActionProcessor[
        GetContainerRegistriesAction, GetContainerRegistriesActionResult
    ]

    def __init__(self, service: ResourceService) -> None:
        self.list_presets = ActionProcessor(service.list_presets)
        self.check_presets = ActionProcessor(service.check_presets)
        self.recalculate_usage = ActionProcessor(service.recalculate_usage)
        self.usage_per_month = ActionProcessor(service.usage_per_month)
        self.usage_per_period = ActionProcessor(service.usage_per_period)
        self.user_month_stats = ActionProcessor(service.user_month_stats)
        self.admin_month_stats = ActionProcessor(service.admin_month_stats)
        self.get_watcher_status = ActionProcessor(service.get_watcher_status)
        self.watcher_agent_start = ActionProcessor(service.watcher_agent_start)
        self.watcher_agent_restart = ActionProcessor(service.watcher_agent_restart)
        self.watcher_agent_stop = ActionProcessor(service.watcher_agent_stop)
        self.get_container_registries = ActionProcessor(service.get_container_registries)
