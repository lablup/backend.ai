from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class AppConfigDefinitionScopeAction(BaseScopeAction):
    """Base for scope-level app config definition actions (create, search)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_DEFINITION


class AppConfigDefinitionScopeActionResult(BaseScopeActionResult):
    pass


class AppConfigDefinitionSingleEntityAction(BaseSingleEntityAction):
    """Base for single-entity app config definition actions (get, purge)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_DEFINITION

    @override
    def field_data(self) -> FieldData | None:
        return None


class AppConfigDefinitionSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
