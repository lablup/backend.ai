from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, OperationType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import PermissionResolutionKey


@dataclass
class ResolveEffectivePermissionsAction(BaseAction):
    """Action to resolve effective permissions across a collection of per-target keys.

    Each key carries one ``(user_id, element_type, entity_id, subject_entity_type)``
    combination. Callers must always provide ``subject_entity_type``, typically
    as ``element_type`` itself. The resolver traverses the scope chain and
    evaluates all role/permission assignments to return all operations the
    user is authorized to perform on each target.
    """

    keys: Collection[PermissionResolutionKey] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveEffectivePermissionsActionResult(BaseActionResult):
    """Result containing the effective permissions per input key."""

    permissions: Mapping[PermissionResolutionKey, frozenset[OperationType]] = field(
        default_factory=dict
    )

    @override
    def entity_id(self) -> str | None:
        return None
