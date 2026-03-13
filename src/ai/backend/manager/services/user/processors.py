from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
    BulkModifyUserAction,
    BulkModifyUserActionResult,
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
from ai.backend.manager.services.user.actions.search_users_by_role import (
    SearchUsersByRoleAction,
    SearchUsersByRoleActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.service import UserService


class UserProcessors(AbstractProcessorPackage):
    # Scope actions with RBAC
    create_user: ScopeActionProcessor[CreateUserAction, CreateUserActionResult]
    search_users_by_domain: ActionProcessor[
        SearchUsersByDomainAction, SearchUsersByDomainActionResult
    ]
    search_users_by_project: ActionProcessor[
        SearchUsersByProjectAction, SearchUsersByProjectActionResult
    ]
    search_users_by_role: ActionProcessor[SearchUsersByRoleAction, SearchUsersByRoleActionResult]
    # Single entity actions with RBAC
    get_user: SingleEntityActionProcessor[GetUserAction, GetUserActionResult]
    modify_user: SingleEntityActionProcessor[ModifyUserAction, ModifyUserActionResult]
    delete_user: SingleEntityActionProcessor[DeleteUserAction, DeleteUserActionResult]
    purge_user: SingleEntityActionProcessor[PurgeUserAction, PurgeUserActionResult]
    # Bulk actions without RBAC (special handling)
    bulk_create_users: ActionProcessor[BulkCreateUserAction, BulkCreateUserActionResult]
    bulk_modify_users: ActionProcessor[BulkModifyUserAction, BulkModifyUserActionResult]
    bulk_purge_users: ActionProcessor[BulkPurgeUserAction, BulkPurgeUserActionResult]
    # Internal/stats actions without RBAC
    user_month_stats: ActionProcessor[UserMonthStatsAction, UserMonthStatsActionResult]
    admin_month_stats: ActionProcessor[AdminMonthStatsAction, AdminMonthStatsActionResult]
    search_users: ActionProcessor[SearchUsersAction, SearchUsersActionResult]

    def __init__(
        self,
        user_service: UserService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Scope actions with RBAC
        self.create_user = ScopeActionProcessor(
            user_service.create_user, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_users_by_domain = ActionProcessor(
            user_service.search_users_by_domain, action_monitors
        )
        self.search_users_by_project = ActionProcessor(
            user_service.search_users_by_project, action_monitors
        )
        self.search_users_by_role = ActionProcessor(
            user_service.search_users_by_role, action_monitors
        )
        # Single entity actions with RBAC
        self.get_user = SingleEntityActionProcessor(
            user_service.get_user, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.modify_user = SingleEntityActionProcessor(
            user_service.modify_user, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.delete_user = SingleEntityActionProcessor(
            user_service.delete_user, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.purge_user = SingleEntityActionProcessor(
            user_service.purge_user, action_monitors, validators=[validators.rbac.single_entity]
        )
        # Bulk actions without RBAC (special handling)
        self.bulk_create_users = ActionProcessor(user_service.bulk_create_users, action_monitors)
        self.bulk_modify_users = ActionProcessor(user_service.bulk_modify_users, action_monitors)
        self.bulk_purge_users = ActionProcessor(user_service.bulk_purge_users, action_monitors)
        # Internal/stats actions without RBAC
        self.user_month_stats = ActionProcessor(user_service.user_month_stats, action_monitors)
        self.admin_month_stats = ActionProcessor(user_service.admin_month_stats, action_monitors)
        self.search_users = ActionProcessor(user_service.search_users, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateUserAction.spec(),
            BulkCreateUserAction.spec(),
            ModifyUserAction.spec(),
            BulkModifyUserAction.spec(),
            DeleteUserAction.spec(),
            GetUserAction.spec(),
            PurgeUserAction.spec(),
            BulkPurgeUserAction.spec(),
            UserMonthStatsAction.spec(),
            AdminMonthStatsAction.spec(),
            SearchUsersAction.spec(),
            SearchUsersByDomainAction.spec(),
            SearchUsersByProjectAction.spec(),
            SearchUsersByRoleAction.spec(),
        ]
