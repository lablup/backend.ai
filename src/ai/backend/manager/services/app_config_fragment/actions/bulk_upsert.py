from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_FRAGMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    ScopeRef,
    ScopeType,
)
from ai.backend.manager.actions.v2.ops.base import AtomicUpsertEntityOpsAction
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.upserters import AppConfigFragmentUpserter


@dataclass
class BulkUpsertAppConfigFragmentsAction(
    AtomicUpsertEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Write the fragments one owner holds, all of them or none.

    Every upserter names the same ``owner``, so one scope answers for the whole write —
    the same scope a create at that owner crosses.
    """

    owner: EntityIdentifier
    upserters: Sequence[AppConfigFragmentUpserter]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_FRAGMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_upsert_app_config_fragments"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=ScopeType(self.owner.entity_type()), scope_id=self.owner),)

    @override
    def to_upserters(self) -> Sequence[AppConfigFragmentUpserter]:
        return self.upserters
