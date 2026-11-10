from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.services.resource_preset.actions.scope_base import (
    ResourcePresetScopeAction,
)


@dataclass
class ListResourcePresetsAction(ResourcePresetScopeAction):
    """List the presets the named scopes offer."""

    access_key: str
    resource_group: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_resource_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListResourcePresetsResult(BaseScopeActionResult):
    # TODO: Add preset type
    presets: list[Any]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
