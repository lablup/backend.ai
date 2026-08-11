from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ResourceRequirementEntry
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class GetModelCardMinResourcesAction(ModelCardAction):
    """Read the minimum resource requirements of the named cards.

    Its own action because the requirements are a table of their own: the card's row
    projection does not carry them, so whoever renders them asks for them, and asks
    for every card at once rather than once per card.
    """

    card_ids: Sequence[UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetModelCardMinResourcesActionResult(BaseActionResult):
    min_resources: dict[UUID, list[ResourceRequirementEntry]]

    @override
    def entity_id(self) -> str | None:
        return None
