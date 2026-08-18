"""DataLookup implementations for the user resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.specs.lookup import DataLookup

__all__ = ("UserResourcePolicyNameLookup",)


@dataclass
class UserResourcePolicyNameLookup(DataLookup[UserResourcePolicyRow, UserResourcePolicyData]):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserResourcePolicyRow.name == self.name]

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
