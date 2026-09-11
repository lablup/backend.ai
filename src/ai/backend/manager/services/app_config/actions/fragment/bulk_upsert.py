from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import AtomicUpsertEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.scopes import AppConfigFragmentOperationScope
from ai.backend.manager.models.app_config_fragment.upserters import AppConfigFragmentUpserter
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class BulkUpsertAppConfigFragmentsAction(
    AtomicUpsertEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Write the fragments one owner holds, all of them or none.

    Every upserter names the same ``owner``, so one scope answers for the whole write —
    the same scope a create at that owner crosses. The owner is existence-checked before
    the write: the row carries no foreign key to it, the owner being a domain or a user.
    """

    owner: EntityIdentifier
    upserters: Sequence[AppConfigFragmentUpserter]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AppConfigFragmentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_upsert_app_config_fragments"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.owner,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (
            AppConfigFragmentOperationScope(
                scope_type=AppConfigScopeType.of_owner(self.owner),
                scope_id=AppConfigScopeID(self.owner),
            ),
        )

    @override
    def to_upserters(self) -> Sequence[AppConfigFragmentUpserter]:
        return self.upserters
