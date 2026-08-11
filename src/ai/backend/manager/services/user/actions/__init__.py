"""User service actions.

Re-exports all action types from submodules.
"""

from .admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from .base import (
    UserAction,
    UserScopeAction,
    UserScopeActionResult,
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)
from .create_user import (
    BulkCreateUserAction,
    BulkCreateUserActionResult,
    CreateUserAction,
    CreateUserActionResult,
    UserCreateSpec,
)
from .delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from .get_user import (
    GetUserAction,
    GetUserActionResult,
)
from .purge_user import (
    BulkPurgeUserAction,
    BulkPurgeUserActionResult,
    PurgeUserAction,
    PurgeUserActionResult,
)
from .search_users import (
    SearchUsersAction,
    SearchUsersActionResult,
)
from .search_users_by_domain import (
    SearchUsersByDomainAction,
    SearchUsersByDomainActionResult,
)
from .search_users_by_project import (
    SearchUsersByProjectAction,
    SearchUsersByProjectActionResult,
)
from .search_users_by_role import (
    SearchUsersByRoleAction,
    SearchUsersByRoleActionResult,
)
from .update_user import (
    BulkUpdateUserAction,
    BulkUpdateUserActionResult,
    UpdateUserAction,
    UpdateUserActionResult,
    UserUpdateSpec,
)
from .user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)

__all__ = (
    "AdminMonthStatsAction",
    "AdminMonthStatsActionResult",
    "BulkCreateUserAction",
    "BulkCreateUserActionResult",
    "BulkUpdateUserAction",
    "BulkUpdateUserActionResult",
    "BulkPurgeUserAction",
    "BulkPurgeUserActionResult",
    "CreateUserAction",
    "CreateUserActionResult",
    "DeleteUserAction",
    "DeleteUserActionResult",
    "GetUserAction",
    "GetUserActionResult",
    "UpdateUserAction",
    "UpdateUserActionResult",
    "PurgeUserAction",
    "PurgeUserActionResult",
    "SearchUsersAction",
    "SearchUsersActionResult",
    "SearchUsersByDomainAction",
    "SearchUsersByDomainActionResult",
    "SearchUsersByProjectAction",
    "SearchUsersByProjectActionResult",
    "SearchUsersByRoleAction",
    "SearchUsersByRoleActionResult",
    "UserAction",
    "UserCreateSpec",
    "UserMonthStatsAction",
    "UserMonthStatsActionResult",
    "UserScopeAction",
    "UserScopeActionResult",
    "UserSingleEntityAction",
    "UserSingleEntityActionResult",
    "UserUpdateSpec",
)
