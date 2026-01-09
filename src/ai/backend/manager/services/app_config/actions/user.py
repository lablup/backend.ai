"""User-level app configuration actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec

from .base import AppConfigAction


@dataclass
class GetUserConfigAction(AppConfigAction):
    """Action to get user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_user"

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_user_config"


@dataclass
class GetUserConfigActionResult(BaseActionResult):
    """Result of get user config action."""

    result: Optional[AppConfigData]

    @override
    def entity_id(self) -> Optional[str]:
        return self.result.scope_id if self.result else None


@dataclass
class UpsertUserConfigAction(AppConfigAction):
    """Action to create or update user-level app configuration."""

    user_id: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_user"

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upsert_user_config"


@dataclass
class UpsertUserConfigActionResult(BaseActionResult):
    """Result of upsert user config action."""

    result: AppConfigData

    @override
    def entity_id(self) -> Optional[str]:
        return self.result.scope_id


@dataclass
class DeleteUserConfigAction(AppConfigAction):
    """Action to delete user-level app configuration."""

    user_id: str

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_user"

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_user_config"


@dataclass
class DeleteUserConfigActionResult(BaseActionResult):
    """Result of delete user config action."""

    deleted: bool
    user_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id if self.deleted else None
