from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, override

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import BulkConditionalUpdater
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkUpdateAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Update many fragments' ``config`` in a single atomic batch (all-or-nothing).

    Carries one ``BulkConditionalUpdater``: each item pairs an ``Updater`` with its own
    allow-list write-gate (``ConditionalUpdater.only_if``) against the target fragment's
    ``(config_name, scope_type)``; ``rank`` is not updatable.
    """

    bulk_updater: BulkConditionalUpdater[AppConfigFragmentRow, AppConfigAllowListRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return [
            AppConfigFragmentBulkTarget(
                fragment_id=cast(AppConfigFragmentID, conditional.updater.pk_value)
            )
            for conditional in self.bulk_updater.updaters
        ]


@dataclass
class BulkUpdateAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
