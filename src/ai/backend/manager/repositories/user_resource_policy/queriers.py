"""DataQuerier implementations for the user resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class UserResourcePolicyQuerier(DataQuerier[UserResourcePolicyRow, UserResourcePolicyData]):
    name: str

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
