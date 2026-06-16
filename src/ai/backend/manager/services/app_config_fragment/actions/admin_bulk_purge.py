from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentKey
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import AppConfigFragmentTarget


@dataclass
class AdminBulkPurgeAppConfigFragmentsAction(BaseBulkAction[AppConfigFragmentTarget]):
    """`keys` carries the parsed natural keys of the rows to purge."""

    keys: list[AppConfigFragmentKey] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def targets(self) -> Sequence[AppConfigFragmentTarget]:
        return [AppConfigFragmentTarget(key=key) for key in self.keys]


@dataclass
class AdminBulkPurgeAppConfigFragmentsActionResult(BaseBulkActionResult):
    purged: list[AppConfigFragmentKey]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [AppConfigFragmentTarget(key=key).to_rbac_element_ref() for key in self.purged]
