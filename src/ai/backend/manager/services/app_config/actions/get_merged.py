"""Get merged configuration action."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import AppConfigAction


@dataclass
class GetMergedAppConfigAction(AppConfigAction):
    """Action to get merged app configuration for a user."""

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
class GetMergedAppConfigActionResult(BaseActionResult):
    """Result of get merged app configuration action."""

    user_id: str
    merged_config: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return self.user_id
