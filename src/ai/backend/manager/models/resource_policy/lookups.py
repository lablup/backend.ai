"""Lookup implementations for the resource policy tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class KeypairResourcePolicyNameLookup(
    DataLookup[KeyPairResourcePolicyRow, KeyPairResourcePolicyUUID]
):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: KeyPairResourcePolicyRow.name == self.name]

    @override
    def to_entity_id(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyUUID:
        return row.uuid


@dataclass
class ProjectResourcePolicyNameLookup(
    DataLookup[ProjectResourcePolicyRow, ProjectResourcePolicyUUID]
):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ProjectResourcePolicyRow.name == self.name]

    @override
    def to_entity_id(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyUUID:
        return row.uuid


@dataclass
class UserResourcePolicyNameLookup(DataLookup[UserResourcePolicyRow, UserResourcePolicyUUID]):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserResourcePolicyRow.name == self.name]

    @override
    def to_entity_id(self, row: UserResourcePolicyRow) -> UserResourcePolicyUUID:
        return row.uuid
