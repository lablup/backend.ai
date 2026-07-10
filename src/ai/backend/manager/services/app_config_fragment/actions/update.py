from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class UpdateAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Update a fragment's ``config`` (replaced wholesale).

    Not admin-only: a user may update their own ``user``-scope fragment. No allow-list
    gate is needed — a fragment row exists only while its ``(config_name, scope_type)``
    allow-list entry does (FK with cascade), so an existing fragment is always writable
    at its own scope.
    """

    updater: Updater[AppConfigFragmentRow]
    requester: UserData | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, str(self.updater.pk_value))


@dataclass
class UpdateAppConfigFragmentActionResult(AppConfigFragmentSingleEntityActionResult):
    fragment: AppConfigFragmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment.id)
