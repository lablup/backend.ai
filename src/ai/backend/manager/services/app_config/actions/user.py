"""User-level app configuration actions."""

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class GetUserConfigAction(AppConfigScopeAction):
    """Action to get user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, self.user_id)


@dataclass
class GetUserConfigActionResult(AppConfigScopeActionResult):
    """Result of get user config action."""

    result: AppConfigData | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.result.scope_id if self.result else ""


@dataclass
class UpsertUserConfigAction(AppConfigScopeAction):
    """Action to create or update user-level app configuration."""

    user_id: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, self.user_id)


@dataclass
class UpsertUserConfigActionResult(AppConfigScopeActionResult):
    """Result of upsert user config action."""

    result: AppConfigData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.result.scope_id


@dataclass
class DeleteUserConfigAction(AppConfigScopeAction):
    """Action to delete user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, self.user_id)


@dataclass
class DeleteUserConfigActionResult(AppConfigScopeActionResult):
    """Result of delete user config action."""

    deleted: bool
    user_id: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return self.user_id
