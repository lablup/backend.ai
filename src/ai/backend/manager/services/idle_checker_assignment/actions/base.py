from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
from ai.backend.manager.actions.action.types import FieldData


class IdleCheckerAssignmentAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IDLE_CHECKER_ASSIGNMENT


class IdleCheckerAssignmentSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IDLE_CHECKER_ASSIGNMENT

    @override
    def field_data(self) -> FieldData | None:
        return None
