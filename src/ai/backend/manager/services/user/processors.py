from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.resource.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.resource.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.service import UserService


class UserProcessors:
    user_month_stats: ActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: ActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]

    def __init__(self, service: UserService) -> None:
        self.user_month_stats = ActionProcessor(service.user_month_stats)
        self.admin_month_stats = ActionProcessor(service.admin_month_stats)
