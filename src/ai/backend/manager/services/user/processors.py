from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.service import UserService


class UserProcessors(AbstractProcessorPackage):
    create_user: ActionProcessor[CreateUserAction, CreateUserActionResult]
    modify_user: ActionProcessor[ModifyUserAction, ModifyUserActionResult]
    delete_user: ActionProcessor[DeleteUserAction, DeleteUserActionResult]
    purge_user: ActionProcessor[PurgeUserAction, PurgeUserActionResult]
    user_month_stats: ActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: ActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]

    def __init__(self, user_service: UserService, action_monitors: list[ActionMonitor]) -> None:
        self.create_user = ActionProcessor(user_service.create_user, action_monitors)
        self.modify_user = ActionProcessor(user_service.modify_user, action_monitors)
        self.delete_user = ActionProcessor(user_service.delete_user, action_monitors)
        self.purge_user = ActionProcessor(user_service.purge_user, action_monitors)
        self.user_month_stats = ActionProcessor(user_service.user_month_stats, action_monitors)
        self.admin_month_stats = ActionProcessor(user_service.admin_month_stats, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateUserAction.spec(),
            ModifyUserAction.spec(),
            DeleteUserAction.spec(),
            PurgeUserAction.spec(),
            UserMonthStatsAction.spec(),
            AdminMonthStatsAction.spec(),
        ]
