import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.services.app_config_fragment.actions.base import AppConfigFragmentAction


@dataclass
class GetUserAppConfigAction(AppConfigFragmentAction):
    """Resolve a single per-user merged AppConfig."""

    user_id: uuid.UUID
    config_name: str

    @override
    def entity_id(self) -> str | None:
        return f"{self.user_id}:{self.config_name}"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetUserAppConfigActionResult(BaseActionResult):
    app_config: AppConfigData

    @override
    def entity_id(self) -> str | None:
        return f"{self.app_config.user_id}:{self.app_config.name}"
