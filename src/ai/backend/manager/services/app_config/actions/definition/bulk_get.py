from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.queriers import (
    BulkAppConfigDefinitionQuerier,
)
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow


@dataclass
class BulkGetAppConfigDefinitionsAction(
    PartialBulkGetEntityOpsAction[AppConfigDefinitionRow, AppConfigDefinitionData]
):
    """Read the registered config names the caller named, answering for each id."""

    ids: Sequence[AppConfigDefinitionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_app_config_definitions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAppConfigDefinitionQuerier:
        return BulkAppConfigDefinitionQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
