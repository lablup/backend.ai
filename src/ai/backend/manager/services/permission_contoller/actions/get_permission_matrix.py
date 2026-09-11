from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import GrantableOperation
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class GetPermissionMatrixAction(RoleAction):
    """Action to get the complete RBAC permission matrix.

    Returns scope -> entity -> operations mapping.
    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetPermissionMatrixActionResult(BaseActionResult):
    """Result of getting the RBAC permission matrix."""

    matrix: Mapping[EntityType, Mapping[EntityType, Sequence[GrantableOperation]]] = field(
        default_factory=dict
    )

    @override
    def entity_id(self) -> str | None:
        return None
