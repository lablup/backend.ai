from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass(frozen=True)
class PartialBulkPurgeAppConfigDefinitionsAction(BasePartialBulkAction):
    """Unregister the named config names with what lies under them, answering for each one."""

    ids: Sequence[AppConfigDefinitionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_app_config_definitions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, ids=[definition_id for definition_id in self.ids if definition_id in allowed]
        )
