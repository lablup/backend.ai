from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey


@dataclass(frozen=True)
class ScopedGetHeldPermissionsAction(BaseScopeAction):
    """The bits one user holds on an entity type within each named scope.

    Answered for by the user's own scope, not by the scopes asked about: the caller
    reads its own state, so a scope it reaches nothing on is an empty answer rather
    than a denial.
    """

    user_id: UserID
    keys: Sequence[GovernCheckKey]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_get_held_permissions"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.user_id]


@dataclass(frozen=True)
class ScopedGetHeldPermissionsActionResult(BaseScopeActionResult):
    granted: Mapping[GovernCheckKey, Permission] = field(default_factory=dict)

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return []
