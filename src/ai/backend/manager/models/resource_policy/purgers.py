"""Delete specs of the three resource policies, keyed by the policy name."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
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
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class KeyPairResourcePolicyPurger(
    EntityPurger[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    name: str
    policy_id: KeyPairResourcePolicyUUID

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class UserResourcePolicyPurger(EntityPurger[UserResourcePolicyRow, UserResourcePolicyData]):
    name: str
    policy_id: UserResourcePolicyUUID

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyPurger(
    EntityPurger[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str
    policy_id: ProjectResourcePolicyUUID

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
