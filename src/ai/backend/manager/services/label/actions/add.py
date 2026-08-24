from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.manager.actions.v2.ops.base import CreateFieldOpsAction
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.label.creators import LabelCreator
from ai.backend.manager.models.label.row import LabelRow


@dataclass
class AddLabelAction(CreateFieldOpsAction[RuntimeEntityID, LabelRow, LabelData]):
    """Put one ``key=value`` on the entity the caller named."""

    owner: RuntimeEntityID
    creator: LabelCreator

    @override
    @classmethod
    def action_name(cls) -> str:
        return "add_label"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def owner_id(self) -> RuntimeEntityID:
        return self.owner

    @override
    def to_creator(self) -> LabelCreator:
        return self.creator
