from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import BulkConditionalCreator
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkCreateAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Create many fragments in a single atomic batch (all-or-nothing).

    Carries one ``BulkConditionalCreator``: each item pairs a fragment ``CreatorSpec`` with its
    own allow-list write-gate (``ConditionalCreator.only_if``). The repository checks every gate
    and inserts all rows in one transaction; a rejected gate or a failed insert rolls back the
    whole batch.
    """

    bulk_creator: BulkConditionalCreator[AppConfigFragmentRow, AppConfigAllowListRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        # Fragments do not exist yet, so there are no per-entity targets to validate.
        return []


@dataclass
class BulkCreateAppConfigFragmentActionResult(AppConfigFragmentBulkActionResult):
    pass
