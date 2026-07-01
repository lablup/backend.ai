from __future__ import annotations

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class AppConfigAllowListScopeAction(BaseScopeAction):
    """Base for scope-level app config allow-list actions (create, search)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_ALLOW_LIST


class AppConfigAllowListScopeActionResult(BaseScopeActionResult):
    pass


class AppConfigAllowListSingleEntityAction(BaseSingleEntityAction):
    """Base for single-entity app config allow-list actions (get, purge)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_ALLOW_LIST

    @override
    def field_data(self) -> FieldData | None:
        return None


class AppConfigAllowListSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
