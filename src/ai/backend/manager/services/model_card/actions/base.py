from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE, ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ModelCardAction(BaseGlobalAction):
    """Base for an operation that names no single model card."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE


@dataclass
class ModelCardScopeAction(BaseScopeAction):
    """Base for a model card read bounded by a scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE


@dataclass
class ModelCardScopeActionResult(BaseScopeActionResult):
    """A scoped model card read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass
class ModelCardSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one model card."""

    model_card_id: ModelCardID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.model_card_id
