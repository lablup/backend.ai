from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.manager.actions.v2.ops.base import UpsertFieldOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.upserters import EntityLabelUpserter


@dataclass
class UpsertEntityLabelAction(
    UpsertFieldOpsAction[RuntimeEntityID, EntityLabelRow, EntityLabelData]
):
    """Set one key on the entity the caller named, replacing the value it carries."""

    owner: RuntimeEntityID
    upserter: EntityLabelUpserter

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_entity_label"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def owner_id(self) -> RuntimeEntityID:
        return self.owner

    @override
    def to_upserter(self) -> EntityLabelUpserter:
        return self.upserter
