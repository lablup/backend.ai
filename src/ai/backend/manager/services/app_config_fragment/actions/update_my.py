from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class UpdateMyAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Self-service path: replace the ``config`` of the caller's own user-scope fragment.

    Update only — no create, no purge. Clearing the fragment is an update with ``{}``.
    """

    fragment_id: AppConfigFragmentID
    user_id: UserID
    config: dict[str, Any]

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
class UpdateMyAppConfigFragmentActionResult(AppConfigFragmentSingleEntityActionResult):
    fragment: AppConfigFragmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment.id)
