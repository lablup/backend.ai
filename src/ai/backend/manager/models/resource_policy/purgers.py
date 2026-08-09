"""Delete specs of the three resource policies, keyed by the policy name."""

from __future__ import annotations

from collections.abc import Sequence
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
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class KeyPairResourcePolicyPurger(
    GlobalEntityPurger[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class UserResourcePolicyPurger(GlobalEntityPurger[UserResourcePolicyRow, UserResourcePolicyData]):
    name: str

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyPurger(
    GlobalEntityPurger[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
