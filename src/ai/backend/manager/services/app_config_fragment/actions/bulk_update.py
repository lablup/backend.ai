from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, override

from ai.backend.common.data.user.types import UserData
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkUpdateAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Update many fragments' ``config`` with per-item partial success (no gate — an existing fragment is always writable at its own scope)."""

    updaters: Sequence[Updater[AppConfigFragmentRow]]
    requester: UserData | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return [
            AppConfigFragmentBulkTarget(fragment_id=cast(AppConfigFragmentID, updater.pk_value))
            for updater in self.updaters
        ]


@dataclass
class BulkUpdateAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
