from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    BulkCreateUserActionResult,
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.get_user import (
    GetUserAction,
    GetUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    BulkPurgeUserActionResult,
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.search_users import (
    SearchUsersAction,
    SearchUsersActionResult,
)
from ai.backend.manager.services.user.actions.search_users_by_domain import (
    SearchUsersByDomainAction,
    SearchUsersByDomainActionResult,
)
from ai.backend.manager.services.user.actions.search_users_by_project import (
    SearchUsersByProjectAction,
    SearchUsersByProjectActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.service import UserService


class UserProcessors(AbstractProcessorPackage):
    create_user: ActionProcessor[CreateUserAction, CreateUserActionResult]
    bulk_create_users: ActionProcessor[BulkCreateUserAction, BulkCreateUserActionResult]
    modify_user: ActionProcessor[ModifyUserAction, ModifyUserActionResult]
    delete_user: ActionProcessor[DeleteUserAction, DeleteUserActionResult]
    get_user: ActionProcessor[GetUserAction, GetUserActionResult]
    purge_user: ActionProcessor[PurgeUserAction, PurgeUserActionResult]
    bulk_purge_users: ActionProcessor[BulkPurgeUserAction, BulkPurgeUserActionResult]
    user_month_stats: ActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: ActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]
    search_users: ActionProcessor[SearchUsersAction, SearchUsersActionResult]
    search_users_by_domain: ActionProcessor[
        SearchUsersByDomainAction, SearchUsersByDomainActionResult
    ]
    search_users_by_project: ActionProcessor[
        SearchUsersByProjectAction, SearchUsersByProjectActionResult
    ]

    def __init__(self, user_service: UserService, action_monitors: list[ActionMonitor]) -> None:
        self.create_user = ActionProcessor(user_service.create_user, action_monitors)
        self.bulk_create_users = ActionProcessor(user_service.bulk_create_users, action_monitors)
        self.modify_user = ActionProcessor(user_service.modify_user, action_monitors)
        self.delete_user = ActionProcessor(user_service.delete_user, action_monitors)
        self.get_user = ActionProcessor(user_service.get_user, action_monitors)
        self.purge_user = ActionProcessor(user_service.purge_user, action_monitors)
        self.bulk_purge_users = ActionProcessor(user_service.bulk_purge_users, action_monitors)
        self.user_month_stats = ActionProcessor(user_service.user_month_stats, action_monitors)
        self.admin_month_stats = ActionProcessor(user_service.admin_month_stats, action_monitors)
        self.search_users = ActionProcessor(user_service.search_users, action_monitors)
        self.search_users_by_domain = ActionProcessor(
            user_service.search_users_by_domain, action_monitors
        )
        self.search_users_by_project = ActionProcessor(
            user_service.search_users_by_project, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateUserAction.spec(),
            BulkCreateUserAction.spec(),
            ModifyUserAction.spec(),
            DeleteUserAction.spec(),
            GetUserAction.spec(),
            PurgeUserAction.spec(),
            BulkPurgeUserAction.spec(),
            UserMonthStatsAction.spec(),
            AdminMonthStatsAction.spec(),
            SearchUsersAction.spec(),
            SearchUsersByDomainAction.spec(),
            SearchUsersByProjectAction.spec(),
        ]
