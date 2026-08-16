"""DataLookup implementations for the keypair resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class KeypairResourcePolicyLookup(DataLookup[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]):
    """Resolves a user into the policy their default keypair is subject to.

    Picks the keypair marked default, else the earliest active one: the marker is
    backfilled only from the former ``main_access_key`` and can be absent.
    """

    user_id: UserID

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: KeyPairResourcePolicyRow.name
            == (
                sa.select(KeyPairRow.resource_policy)
                .where(KeyPairRow.user == self.user_id)
                .where(KeyPairRow.is_active.is_(True))
                .order_by(
                    KeyPairRow.is_default.desc(),
                    KeyPairRow.created_at.asc(),
                    KeyPairRow.access_key.asc(),
                )
                .limit(1)
                .scalar_subquery()
            )
        ]

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()
