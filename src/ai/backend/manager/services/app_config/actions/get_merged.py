"""Get merged configuration action."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult

from .base import AppConfigAction


@dataclass
class GetMergedAppConfigAction(AppConfigAction):
    """Action to get merged app configuration for a user."""

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
        return "get_merged_app_config"


@dataclass
class GetMergedAppConfigActionResult(BaseActionResult):
    """Result of get merged app configuration action."""

    user_id: str
    merged_config: Mapping[str, Any]

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id
