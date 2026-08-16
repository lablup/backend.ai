"""DataLookup implementations for the user resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserResourcePolicyLookup(DataLookup[UserResourcePolicyRow, UserResourcePolicyData]):
    """Resolves the user a policy applies to into the policy itself.

    The policy row carries no owner column, so the key is read off the user.
    """

    user_id: UserID

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: UserResourcePolicyRow.name
            == (
                sa.select(UserRow.resource_policy)
                .where(UserRow.uuid == self.user_id)
                .scalar_subquery()
            )
        ]

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
