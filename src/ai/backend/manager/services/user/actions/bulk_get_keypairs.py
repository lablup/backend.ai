from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.queriers import BulkKeypairQuerier
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupBulkKeypairOwnerAction,
)


@dataclass
class BulkGetKeypairsAction(
    PartialBulkGetFieldOpsAction[KeyPairID, UserID, KeyPairRow, KeyPairData]
):
    """Read the keypairs the caller named."""

    ids: Sequence[KeyPairID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_keypairs"

    @override
    def field_ids(self) -> Sequence[KeyPairID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKeypairOwnerAction:
        return LookupBulkKeypairOwnerAction(keypair_ids=self.ids)

    @override
    def to_querier(self) -> BulkKeypairQuerier:
        return BulkKeypairQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KeyPairID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
