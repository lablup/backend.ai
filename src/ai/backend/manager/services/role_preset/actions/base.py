from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class RolePresetAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE


@dataclass
class RolePresetBulkAction(RolePresetAction):
    """Base for actions that operate on multiple role presets at once.

    Bulk operations target a set of presets rather than a single entity, so
    there is no single entity id to report.
    """

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class RolePresetScopeAction(RolePresetAction):
    """Base for actions scoped to a collection of role presets (e.g. search).

    Scope operations query within an RBAC scope rather than acting on one
    entity, so there is no single entity id to report.
    """

    @override
    def entity_id(self) -> str | None:
        return None
