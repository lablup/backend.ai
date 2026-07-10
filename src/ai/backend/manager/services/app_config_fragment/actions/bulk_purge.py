from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, override

from ai.backend.common.data.user.types import UserData
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import Purger
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkPurgeAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Purge many fragments with per-item partial success (no gate — purging the allow-list entry itself cascades to its fragments separately)."""

    purgers: Sequence[Purger[AppConfigFragmentRow]]
    requester: UserData | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return [
            AppConfigFragmentBulkTarget(fragment_id=cast(AppConfigFragmentID, purger.pk_value))
            for purger in self.purgers
        ]


@dataclass
class BulkPurgeAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
