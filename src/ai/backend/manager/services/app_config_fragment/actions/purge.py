from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import ExistsQuerier, Purger
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class PurgeAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Purge a fragment — not admin-only.

    Gated by the allow-list write-gate (``only_if``) against the fragment's
    ``(config_name, scope_type)``, so an allow-listed user may purge their own
    ``user``-scope fragment.
    """

    purger: Purger[AppConfigFragmentRow]
    only_if: ExistsQuerier[AppConfigAllowListRow]
    """Allow-list write-gate: the purge is committed only if this existence check passes.

    Built by the caller (e.g. the API adapter) and enforced atomically by the repository
    within the write transaction.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, str(self.purger.pk_value))


@dataclass
class PurgeAppConfigFragmentActionResult(AppConfigFragmentSingleEntityActionResult):
    fragment: AppConfigFragmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment.id)
