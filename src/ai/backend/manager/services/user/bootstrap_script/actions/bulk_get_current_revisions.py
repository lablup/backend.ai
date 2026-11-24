from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBulkBootstrapScriptOwnerAction,
)


@dataclass(frozen=True)
class BulkGetCurrentBootstrapScriptRevisionsAction(
    BasePartialBulkFieldAction[BootstrapScriptID, RuntimeEntityID]
):
    """Read the latest revision of each named script, which is its current content."""

    script_ids: Sequence[BootstrapScriptID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_current_bootstrap_script_revisions"

    @override
    def field_ids(self) -> Sequence[BootstrapScriptID]:
        return tuple(self.script_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkBootstrapScriptOwnerAction:
        return LookupBulkBootstrapScriptOwnerAction(script_ids=self.script_ids)

    @override
    def narrowed_to(self, field_ids: Sequence[BootstrapScriptID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self, script_ids=[script_id for script_id in self.script_ids if script_id in allowed]
        )
