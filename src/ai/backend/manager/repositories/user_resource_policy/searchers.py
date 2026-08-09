"""Searcher implementations for the user resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class UserResourcePolicySearcher(Searcher[UserResourcePolicyRow, UserResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(UserResourcePolicyRow)

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
