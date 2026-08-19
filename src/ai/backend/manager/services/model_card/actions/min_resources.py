from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ResourceRequirementEntry
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class GetModelCardMinResourcesAction(ModelCardAction):
    """Read the minimum resource requirements of the named cards.

    Its own action because the requirements are a table of their own, asked for every
    card at once rather than once per card.
    """

    card_ids: Sequence[UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_model_card_min_resources"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetModelCardMinResourcesActionResult:
    min_resources: dict[UUID, list[ResourceRequirementEntry]]
