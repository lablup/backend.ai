"""Searcher implementations for the resource policy tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.resource_policy.query_spec import (
    KeyPairResourcePolicyQuerySpec,
    ProjectResourcePolicyQuerySpec,
    UserResourcePolicyQuerySpec,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KeyPairResourcePolicySearcher(Searcher[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairResourcePolicyRow)

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyQuerySpec.own.to_data(row)


@dataclass
class ProjectResourcePolicySearcher(Searcher[ProjectResourcePolicyRow, ProjectResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ProjectResourcePolicyRow)

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return ProjectResourcePolicyQuerySpec.own.to_data(row)


@dataclass
class UserResourcePolicySearcher(Searcher[UserResourcePolicyRow, UserResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(UserResourcePolicyRow)

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return UserResourcePolicyQuerySpec.own.to_data(row)
