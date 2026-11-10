"""Lookup implementations for the resource policy tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyEntityType,
    ProjectResourcePolicyUUID,
    UserResourcePolicyEntityType,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.lookup import BulkDataLookup, DataLookup


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
    def entity_type(self) -> EntityType:
        return KeyPairResourcePolicyEntityType()

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
    def entity_type(self) -> EntityType:
        return ProjectResourcePolicyEntityType()

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
    def entity_type(self) -> EntityType:
        return UserResourcePolicyEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserResourcePolicyRow.name == self.name]

    @override
    def to_entity_id(self, row: UserResourcePolicyRow) -> UserResourcePolicyUUID:
        return row.uuid


@dataclass
class KeypairResourcePolicyNamesLookup(BulkDataLookup[str, KeyPairResourcePolicyUUID]):
    """Resolves several names into the policies they name."""

    @override
    def build_query(self, keys: Sequence[str]) -> sa.sql.Select[Any]:
        return sa.select(KeyPairResourcePolicyRow.name, KeyPairResourcePolicyRow.uuid).where(
            KeyPairResourcePolicyRow.name.in_(keys)
        )

    @override
    def to_entity_id(self, value: UUID) -> KeyPairResourcePolicyUUID:
        return KeyPairResourcePolicyUUID(value)


@dataclass
class ProjectResourcePolicyNamesLookup(BulkDataLookup[str, ProjectResourcePolicyUUID]):
    """Resolves several names into the policies they name."""

    @override
    def build_query(self, keys: Sequence[str]) -> sa.sql.Select[Any]:
        return sa.select(ProjectResourcePolicyRow.name, ProjectResourcePolicyRow.uuid).where(
            ProjectResourcePolicyRow.name.in_(keys)
        )

    @override
    def to_entity_id(self, value: UUID) -> ProjectResourcePolicyUUID:
        return ProjectResourcePolicyUUID(value)


@dataclass
class UserResourcePolicyNamesLookup(BulkDataLookup[str, UserResourcePolicyUUID]):
    """Resolves several names into the policies they name."""

    @override
    def build_query(self, keys: Sequence[str]) -> sa.sql.Select[Any]:
        return sa.select(UserResourcePolicyRow.name, UserResourcePolicyRow.uuid).where(
            UserResourcePolicyRow.name.in_(keys)
        )

    @override
    def to_entity_id(self, value: UUID) -> UserResourcePolicyUUID:
        return UserResourcePolicyUUID(value)
