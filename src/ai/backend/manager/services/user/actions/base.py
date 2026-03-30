from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class UserAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER


class UserScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER


class UserScopeActionResult(BaseScopeActionResult):
    pass


class UserSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER

    @override
    def field_data(self) -> FieldData | None:
        return None


class UserSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
