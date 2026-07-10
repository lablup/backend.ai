from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkActionResult,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BulkCreateAppConfigFragmentAction(AppConfigFragmentBulkAction):
    """Create many fragments with per-item partial success; the FK to the allow-list gates each write."""

    creator_specs: Sequence[AppConfigFragmentCreatorSpec]
    requester: UserData | None = None

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
