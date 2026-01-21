"""Actions for app configuration service."""

from .base import AppConfigAction
from .domain import (
    DeleteDomainConfigAction,
    DeleteDomainConfigActionResult,
    GetDomainConfigAction,
    GetDomainConfigActionResult,
    UpsertDomainConfigAction,
    UpsertDomainConfigActionResult,
)
from .get_merged import GetMergedAppConfigAction, GetMergedAppConfigActionResult
from .user import (
    DeleteUserConfigAction,
    DeleteUserConfigActionResult,
    GetUserConfigAction,
    GetUserConfigActionResult,
    UpsertUserConfigAction,
    UpsertUserConfigActionResult,
)

__all__ = [
    "AppConfigAction",
    # Domain config actions
    "GetDomainConfigAction",
    "GetDomainConfigActionResult",
    "UpsertDomainConfigAction",
    "UpsertDomainConfigActionResult",
    "DeleteDomainConfigAction",
    "DeleteDomainConfigActionResult",
    # User config actions
    "GetUserConfigAction",
    "GetUserConfigActionResult",
    "UpsertUserConfigAction",
    "UpsertUserConfigActionResult",
    "DeleteUserConfigAction",
    "DeleteUserConfigActionResult",
    # Merged config action
    "GetMergedAppConfigAction",
    "GetMergedAppConfigActionResult",
]
