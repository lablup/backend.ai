from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class TemplateAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_TEMPLATE


class TemplateScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_TEMPLATE


class TemplateScopeActionResult(BaseScopeActionResult):
    pass


class TemplateSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_TEMPLATE

    @override
    def field_data(self) -> FieldData | None:
        return None


class TemplateSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
