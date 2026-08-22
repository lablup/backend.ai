"""Querier implementations for the resource policy tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
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
    uuid: KeyPairResourcePolicyUUID

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairResourcePolicyRow.uuid

    @override
    def entity_id_value(self) -> KeyPairResourcePolicyUUID:
        return self.uuid

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyQuerier(
    DataQuerier[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    uuid: ProjectResourcePolicyUUID

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectResourcePolicyRow.uuid

    @override
    def entity_id_value(self) -> ProjectResourcePolicyUUID:
        return self.uuid

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()


@dataclass
class UserResourcePolicyQuerier(DataQuerier[UserResourcePolicyRow, UserResourcePolicyData]):
    uuid: UserResourcePolicyUUID

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return UserResourcePolicyRow.uuid

    @override
    def entity_id_value(self) -> UserResourcePolicyUUID:
        return self.uuid

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
