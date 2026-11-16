from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.queriers import BulkBootstrapScriptQuerier
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBulkBootstrapScriptOwnerAction,
)


@dataclass
class BulkGetBootstrapScriptsAction(
    PartialBulkGetFieldOpsAction[
        BootstrapScriptID, RuntimeEntityID, BootstrapScriptRow, BootstrapScriptData
    ]
):
    """Read the bootstrap scripts the caller named."""

    ids: Sequence[BootstrapScriptID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_bootstrap_scripts"

    @override
    def field_ids(self) -> Sequence[BootstrapScriptID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkBootstrapScriptOwnerAction:
        return LookupBulkBootstrapScriptOwnerAction(script_ids=self.ids)

    @override
    def to_querier(self) -> BulkBootstrapScriptQuerier:
        return BulkBootstrapScriptQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[BootstrapScriptID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
