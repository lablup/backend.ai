from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class AppConfigFragmentScopeAction(BaseScopeAction):
    """Base for scope-level app config fragment actions (create, search)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT


class AppConfigFragmentScopeActionResult(BaseScopeActionResult):
    pass


class AppConfigFragmentSingleEntityAction(BaseSingleEntityAction):
    """Base for single-entity app config fragment actions (get, update, purge)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_FRAGMENT

    @override
    def field_data(self) -> FieldData | None:
        return None


class AppConfigFragmentSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
