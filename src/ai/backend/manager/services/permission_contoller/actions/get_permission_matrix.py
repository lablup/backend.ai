from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.permission.types import GrantableOperation


@dataclass(frozen=True)
class PublicGetPermissionMatrixAction(BaseGlobalAction):
    """The scope, entity and operation combinations a role may be given.

    Read off the wired catalog, so it carries no row any caller owns.
    """

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
        return "public_get_permission_matrix"


@dataclass(frozen=True)
class PublicGetPermissionMatrixActionResult:
    matrix: Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]] = field(
        default_factory=dict
    )
