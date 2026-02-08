"""User-level app configuration actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec

from .base import AppConfigAction


@dataclass
class GetUserConfigAction(AppConfigAction):
    """Action to get user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_USER

    @override
    def entity_id(self) -> str | None:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetUserConfigActionResult(BaseActionResult):
    """Result of get user config action."""

    result: AppConfigData | None

    @override
    def entity_id(self) -> str | None:
        return self.result.scope_id if self.result else None


@dataclass
class UpsertUserConfigAction(AppConfigAction):
    """Action to create or update user-level app configuration."""

    user_id: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_USER

    @override
    def entity_id(self) -> str | None:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpsertUserConfigActionResult(BaseActionResult):
    """Result of upsert user config action."""

    result: AppConfigData

    @override
    def entity_id(self) -> str | None:
        return self.result.scope_id


@dataclass
class DeleteUserConfigAction(AppConfigAction):
    """Action to delete user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_USER

    @override
    def entity_id(self) -> str | None:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteUserConfigActionResult(BaseActionResult):
    """Result of delete user config action."""

    deleted: bool
    user_id: str

    @override
    def entity_id(self) -> str | None:
        return self.user_id if self.deleted else None
