from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentSingleEntityAction,
    AppConfigFragmentSingleEntityActionResult,
)


@dataclass
class PurgeAppConfigFragmentAction(AppConfigFragmentSingleEntityAction):
    """Purge a fragment — not admin-only.

    No allow-list gate is needed — a fragment row exists only while its
    ``(config_name, scope_type)`` allow-list entry does (FK with cascade), so an
    existing fragment is always removable at its own scope. Purging the allow-list
    entry itself cascades to its fragments without going through this action.
    """

    purger_spec: AppConfigFragmentPurgerSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger_spec.fragment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return self.purger_spec.entity_ref()


@dataclass
class PurgeAppConfigFragmentActionResult(AppConfigFragmentSingleEntityActionResult):
    fragment: AppConfigFragmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.fragment.id)
