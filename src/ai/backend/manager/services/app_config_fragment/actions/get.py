from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
)
from ai.backend.manager.services.app_config_fragment.actions.base import AppConfigFragmentAction


@dataclass
class GetAppConfigFragmentAction(AppConfigFragmentAction):
    key: AppConfigFragmentKey

    @override
    def entity_id(self) -> str | None:
        # Row id is not known at action time (lookup is by natural key).
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAppConfigFragmentActionResult(BaseActionResult):
    fragment: AppConfigFragmentData

    @override
    def entity_id(self) -> str | None:
        return str(self.fragment.id)
