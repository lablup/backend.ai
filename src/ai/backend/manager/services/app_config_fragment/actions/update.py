from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import ExistsQuerier, Updater
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class UpdateAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Update a fragment's ``config`` (replaced wholesale); ``rank`` is not updatable.

    Not admin-only: an allow-listed user may update their own ``user``-scope fragment. The
    allow-list write-gate (``only_if``) authorizes the write against the fragment's
    ``(config_name, scope_type)``.
    """

    updater: Updater[AppConfigFragmentRow]
    only_if: ExistsQuerier[AppConfigAllowListRow]
    """Allow-list write-gate: the update is committed only if this existence check passes.

    Built by the caller (e.g. the API adapter) and enforced atomically by the repository
    within the write transaction.
    """

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
