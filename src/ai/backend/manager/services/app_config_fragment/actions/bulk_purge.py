from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.app_config_fragment.purgers import (
    AppConfigFragmentPurgerSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkPurgeAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Purge many fragments with per-item partial success (no gate — purging the allow-list entry itself cascades to its fragments separately)."""

    purger_specs: Sequence[AppConfigFragmentPurgerSpec]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return [
            AppConfigFragmentBulkTarget(fragment_id=spec.fragment_id) for spec in self.purger_specs
        ]


@dataclass
class BulkPurgeAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
