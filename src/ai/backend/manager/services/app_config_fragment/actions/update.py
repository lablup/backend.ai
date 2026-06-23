from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class UpdateAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Admin path: update a fragment at any scope (config replace and/or rank re-order)."""

    fragment_id: AppConfigFragmentID
    updater_spec: AppConfigFragmentUpdaterSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, str(self.fragment_id))


@dataclass
class UpdateAppConfigFragmentActionResult(AppConfigFragmentSingleEntityActionResult):
    fragment: AppConfigFragmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment.id)
