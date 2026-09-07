from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass
class BulkDeleteModelCardAction(BasePartialBulkAction):
    """Delete the named model cards, answering for each one.

    ``PURGE`` because the row is removed rather than marked deleted, which is also
    what the cascade behind ``options`` acts on.
    """

    ids: Sequence[ModelCardID]
    options: DeleteModelCardOptions

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_model_card"

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
        return replace(self, ids=[card_id for card_id in self.ids if card_id in allowed])
