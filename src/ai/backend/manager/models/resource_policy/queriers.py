"""Querier implementations for the resource policy tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class KeyPairResourcePolicyQuerier(
    DataQuerier[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyQuerier(
    DataQuerier[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()


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
